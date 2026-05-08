import serial
import time

class ECGTest:
    def __init__(self, port='COM3'):
        self.port = port
        self.ser = None

    def run_test(self):
        print(f"--- TENTATIVO TEST ECG SU {self.port} ---")
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=2)
            self.ser.write(b'\x01') # Stop
            time.sleep(0.5)
            self.ser.reset_input_buffer()
            self.ser.write(b'\x07') # Start
            print("Streaming avviato. Leggo i dati...")
            
            for i in range(30):
                if self.ser.read(1) == b'\x00':
                    raw = self.ser.read(11) 
                    # ECG 24-bit è ai byte 5,6,7 del payload (dopo header e TS)
                    val = int.from_bytes(raw[4:7], byteorder='little', signed=True)
                    print(f"[{i}] Valore ECG: {val}")
                time.sleep(0.01)
            
            self.ser.write(b'\x01')
            print("Test ECG OK.")
        except Exception as e:
            print(f"ERRORE: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

if __name__ == "__main__":
    ECGTest().run_test()