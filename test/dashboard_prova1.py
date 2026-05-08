import serial
import time
import threading
import sys
import streamlit as st
import io
import contextlib
from collections import deque
from pyshimmer import ShimmerBluetooth, DEFAULT_BAUDRATE, DataPacket
from pyshimmer.bluetooth.bt_api import BluetoothRequestHandler, RequestCompletion
from pyshimmer.dev.channels import ESensorGroup, EChannelType, ChDataTypeAssignment
from pyshimmer.util import fmt_hex

# --- CONFIGURAZIONE ---
COM_ECG = "COM3"
COM_IMU = "COM6"

# ============================================================
# PATCH RUNTIME
# ============================================================
def _patched_process_resp_from_queue(self):
    try:
        cmd, return_obj = self._resp_queue.get_nowait()
    except Exception:
        return
    resp_code = cmd.get_response_code()
    peek = self._serial.peek(len(resp_code))
    if peek != resp_code:
        raise ValueError(f"Expecting {fmt_hex(resp_code)} but found {fmt_hex(peek)}")
    result = cmd.receive(self._serial)
    return_obj.set_result(result)

BluetoothRequestHandler._process_resp_from_queue = _patched_process_resp_from_queue

def _patched_process_ack(self):
    try:
        self._serial.read_ack()
    except Exception:
        return
    try:
        compl_obj, cmd_resp_pair = self._ack_queue.get_nowait()
        if None not in cmd_resp_pair:
            self._resp_queue.put_nowait(cmd_resp_pair)
        compl_obj.set_completed()
    except Exception:
        pass  # ACK non atteso — ignorato

BluetoothRequestHandler._process_ack = _patched_process_ack

def safe_print(messaggio):
    try:
        print(messaggio)
        sys.stdout.flush()
    except Exception:
        pass

# ============================================================
# GESTORE HARDWARE
# ============================================================
class HardwareManager:
    def __init__(self):
        # La metrica mostrata all'utente
        self.bpm_display = 0
        # Una memoria per stabilizzare il calcolo del BPM (media mobile)
        self.bpm_buffer = deque([70] * 4, maxlen=4)
        
        self.activity_level = 0
        self.ecg_history = deque([0] * 500, maxlen=500)
        self.imu_history = deque([0] * 500, maxlen=500)
        self.ecg_status = "🔴 In attesa..."
        self.imu_status = "🔴 In attesa..."
        self.running = True
        self.imu_offset = 0
        
        self.data_lock = threading.Lock()
        self._imu_initialized = False
        self._ultimo_pacchetto = time.time()

_MANAGER = HardwareManager()

ECG_MANUAL_TYPES = [
    EChannelType.TIMESTAMP,
    EChannelType.EXG_ADS1292R_1_CH1_24BIT,
    EChannelType.EXG_ADS1292R_1_CH2_24BIT,
    EChannelType.EXG_ADS1292R_2_CH1_24BIT,
    EChannelType.EXG_ADS1292R_2_CH2_24BIT,
]
ECG_STREAM_TYPES = [(t, ChDataTypeAssignment[t]) for t in ECG_MANUAL_TYPES]

# ============================================================
# WORKER DEL SENSORE
# ============================================================
def sensor_worker(port, sensor_type, manager):
    while manager.running:
        ser = None
        shim_dev = None
        try:
            safe_print(f"[{sensor_type}] Apertura {port}...")
            ser = serial.Serial(port, DEFAULT_BAUDRATE, timeout=1.0)
            safe_print(f"[{sensor_type}] Porta aperta OK")

            for _ in range(3):
                ser.write(b"\x01")
                time.sleep(0.3)
                ser.reset_input_buffer()
                ser.reset_output_buffer()
            time.sleep(0.5)
            ser.reset_input_buffer()

            ser.timeout = 2.0
            with contextlib.redirect_stderr(io.StringIO()):
                shim_dev = ShimmerBluetooth(ser)
                shim_dev.initialize()
            safe_print(f"[{sensor_type}] Initialize OK")

            if sensor_type == "IMU":
                shim_dev.set_sensors([ESensorGroup.ACCEL_LN])
                safe_print(f"[IMU] Canali configurati OK")
                manager.imu_status = "✅ IMU Connesso"
            else:
                manager.ecg_status = "✅ ECG Connesso"

            val_prec = 0
            ultimo_battito = time.time()
            base_line = None 
            stampato = False

            def handler(pkt: DataPacket) -> None:
                nonlocal val_prec, ultimo_battito, base_line, stampato
                
                with manager.data_lock:
                    manager._ultimo_pacchetto = time.time()

                if sensor_type == "ECG":
                    if not stampato:
                        safe_print(f"[ECG] Primo pacchetto OK, canali: {list(pkt._values.keys())}")
                        stampato = True
                        
                    for ch_key, val_raw in pkt._values.items():
                        ch_str = str(ch_key).upper()
                        if "CH2_24BIT" in ch_str and "ADS1292R_1" in ch_str:
                            if base_line is None:
                                base_line = val_raw
                            else:
                                base_line = 0.85 * base_line + 0.15 * val_raw
                            
                            val_f = val_raw - base_line
                            
                            ora = time.time()
                            delta = abs(val_f - val_prec)
                            
                            # Logica BPM con Media Mobile
                            if delta > 150000 and (ora - ultimo_battito) > 0.4:
                                bpm_instant = 60 / max(0.01, ora - ultimo_battito)
                                bpm_constrained = max(40, min(200, int(bpm_instant)))
                                
                                with manager.data_lock:
                                    manager.bpm_buffer.append(bpm_constrained)
                                    # La metrica effettiva è la media degli ultimi 4 battiti
                                    manager.bpm_display = int(sum(manager.bpm_buffer) / len(manager.bpm_buffer))
                                
                                ultimo_battito = ora
                            
                            with manager.data_lock:
                                manager.ecg_history.append(val_f)
                                
                            val_prec = val_f
                            break
                else:
                    x, y, z = 0, 0, 0
                    found = False
                    for ch_key, val in pkt._values.items():
                        ch_str = str(ch_key).upper()
                        if "ACCEL" in ch_str:
                            if "X" in ch_str: x = val
                            elif "Y" in ch_str: y = val
                            elif "Z" in ch_str: z = val
                            found = True
                            
                    if found:
                        mov = int((x**2 + y**2 + z**2) ** 0.5)
                        if not manager._imu_initialized:
                            manager.imu_offset = mov
                            manager._imu_initialized = True
                        else:
                            manager.imu_offset = 0.99 * manager.imu_offset + 0.01 * mov
                        
                        diff = abs(mov - manager.imu_offset)
                        manager.activity_level = int(diff) if diff > 80 else 0
                        
                        with manager.data_lock:
                            manager.imu_history.append(manager.activity_level)

            # --- Avvio streaming ---
            if sensor_type == "ECG":
                shim_dev._bluetooth.set_stream_types(ECG_STREAM_TYPES)
                shim_dev.add_stream_callback(handler)
                compl_obj = RequestCompletion()
                shim_dev._bluetooth._ack_queue.put_nowait((compl_obj, (None, None)))
                safe_print(f"[ECG] Invio START_STREAMING raw (0x70)...")
                shim_dev._serial._serial.write(b'\x70')
                shim_dev._serial._serial.flush()
                safe_print(f"[ECG] Streaming avviato")
            else:
                shim_dev.add_stream_callback(handler)
                shim_dev.start_streaming()

            # --- Loop monitoraggio watchdog ---
            while manager.running:
                with manager.data_lock:
                    time_since_packet = time.time() - manager._ultimo_pacchetto
                if time_since_packet > 30.0:
                    raise ConnectionError("Timeout dati Bluetooth")
                time.sleep(0.5)

        except (serial.SerialException, ConnectionError, TimeoutError, ValueError) as e:
            safe_print(f"[{sensor_type}] Errore: {type(e).__name__}: {e}")
            if sensor_type == "ECG":
                manager.ecg_status = "🔄 Riconnessione ECG..."
            else:
                manager.imu_status = "🔄 Riconnessione IMU..."
        except Exception as e:
            safe_print(f"[{sensor_type}] Errore inatteso: {type(e).__name__}: {e}")
        finally:
            if shim_dev:
                try:
                    shim_dev.stop_streaming()
                    shim_dev.shutdown()
                    safe_print(f"[{sensor_type}] Chiusura OK")
                except Exception:
                    pass
            elif ser and ser.is_open:
                try:
                    ser.close()
                except Exception:
                    pass
        time.sleep(5)

# ============================================================
# AVVIO THREAD 
# ============================================================
def _avvia_se_non_esiste(port, sensor_type):
    nome = f"shimmer-{sensor_type}"
    for t in threading.enumerate():
        if t.name == nome and t.is_alive():
            safe_print(f"[Modulo] Thread {sensor_type} già attivo, skip")
            return t
    t = threading.Thread(
        target=sensor_worker,
        args=(port, sensor_type, _MANAGER),
        daemon=True,
        name=nome,
    )
    t.start()
    safe_print(f"[Modulo] Thread {sensor_type} avviato")
    return t

# ============================================================
# INTERFACCIA STREAMLIT
# ============================================================
def main():
    st.set_page_config(page_title="Dashboard Shimmer Live", layout="wide")
    st.title("🛰️ Monitoraggio Biometrico Live")

    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        _avvia_se_non_esiste(COM_ECG, "ECG")
        _avvia_se_non_esiste(COM_IMU, "IMU")

    # Copia sicura dei dati sotto Lock
    with _MANAGER.data_lock:
        ecg_data = list(_MANAGER.ecg_history)
        imu_data = list(_MANAGER.imu_history)
        bpm_current = _MANAGER.bpm_display
        activity_current = _MANAGER.activity_level
        ecg_status = _MANAGER.ecg_status
        imu_status = _MANAGER.imu_status

    # Renderizzazione statica nativa di Streamlit (Nessun ciclo while!)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Frequenza Cardiaca", f"{bpm_current} BPM", ecg_status)
        st.line_chart(ecg_data, height=300)
    with c2:
        st.metric("Attività", activity_current, imu_status)
        st.area_chart(imu_data, height=300)

    # Il trucco standard per le dashboard live su Streamlit: 
    # aspetta mezzo secondo e ricarica se stesso
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()