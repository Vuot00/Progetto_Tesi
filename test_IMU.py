import serial
import time

class IMUTest:
    def __init__(self, port='COM6'): # <--- INSERISCI LA NUOVA PORTA
        self.port = port
        self.ser = None

    def run_test(self):
        print(f"--- AVVIO TEST IMU SU {self.port} ---")
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=2)
            self.ser.write(b'\x01')
            time.sleep(0.5)
            self.ser.reset_input_buffer()
            self.ser.write(b'\x07')
            print("Streaming avviato correttamente.")
            
            for i in range(20):
                if self.ser.read(1) == b'\x00':
                    raw = self.ser.read(9) # Payload 10 byte (1 header + 9 dati)
                    # Accelerometro X (2 byte)
                    x = int.from_bytes(raw[2:4], byteorder='little', signed=True)
                    print(f"Accel X [{i}]: {x}")
            
            self.ser.write(b'\x01')
            print("--- TEST COMPLETATO ---")
        except Exception as e:
            print(f"ERRORE: {e}")
        finally:
            if self.ser: self.ser.close()

if __name__ == "__main__":
    IMUTest().run_test()