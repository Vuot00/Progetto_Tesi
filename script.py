import serial
import time
import signal
import sys

HEADER = 0x00
SIZE_PKT = 16

ser = None

def chiudi():
    print("Chiusura pulita...")
    try:
        ser.write(b"\x01")
        time.sleep(0.1)
    except Exception:
        pass
    try:
        ser.close()
    except Exception:
        pass
    print("Porta chiusa.")

def handler_signal(sig, frame):
    chiudi()
    sys.exit(0)

signal.signal(signal.SIGINT, handler_signal)
signal.signal(signal.SIGTERM, handler_signal)

ser = serial.Serial("COM5", 115200, timeout=0.1)
time.sleep(0.5)
ser.reset_input_buffer()
ser.reset_output_buffer()
ser.write(b"\x01")
time.sleep(0.3)
ser.reset_input_buffer()
ser.reset_output_buffer()
time.sleep(0.3)
ser.reset_input_buffer()

ser.write(b"\x07")
print("Streaming avviato, in ascolto...")

data_buffer = bytearray()
debug_count = 0
ultimo_pkt = time.time()
start = time.time()

while time.time() - start < 10:
    if ser.in_waiting > 0:
        data_buffer.extend(ser.read(ser.in_waiting))

    while len(data_buffer) >= SIZE_PKT:
        if data_buffer[0] == HEADER:
            raw = data_buffer[:SIZE_PKT]
            ora = time.time()
            intervallo = (ora - ultimo_pkt) * 1000
            ultimo_pkt = ora
            if debug_count < 20:
                ts = int.from_bytes(raw[1:4], byteorder='little')
                status1 = raw[6]
                ch1 = int.from_bytes(raw[7:10], byteorder='big', signed=True)
                ch2 = int.from_bytes(raw[10:13], byteorder='big', signed=True)
                print(f"ts={ts} status={status1:#x} ch1={ch1} ch2={ch2}")
                debug_count += 1
            data_buffer = data_buffer[SIZE_PKT:]
        else:
            try:
                next_h = data_buffer.index(HEADER, 1)
                data_buffer = data_buffer[next_h:]
            except ValueError:
                data_buffer.clear()

    time.sleep(0.01)

chiudi()