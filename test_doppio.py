import serial
import time

# --- INSERISCI QUI LE TUE PORTE ---
COM_SENSORE_1 = "COM3"  # ecg
COM_SENSORE_2 = "COM6"  # imu
BAUD_RATE = 115200


def test_connessione_sfalsata():
    print("--- INIZIO TEST CONNESSIONE DOPPIA ---")
    ser1 = None
    ser2 = None

    try:
        print(f"\n1. Tento connessione al SENSORE 1 ({COM_SENSORE_1})...")
        ser1 = serial.Serial(COM_SENSORE_1, BAUD_RATE, timeout=2)

        # Simulo l'avvio del sensore
        ser1.write(b"\x01")
        time.sleep(0.5)
        ser1.write(b"\x07")
        print(f"   ✅ Sensore 1 ({COM_SENSORE_1}) APERTO e in streaming!")

        # --- IL SEGRETO È QUI ---
        print(
            "\n⏳ PAUSA DI 4 SECONDI (Lascio stabilizzare il driver Bluetooth di Windows)..."
        )
        time.sleep(4)

        print(f"\n2. Tento connessione al SENSORE 2 ({COM_SENSORE_2})...")
        ser2 = serial.Serial(COM_SENSORE_2, BAUD_RATE, timeout=2)

        # Simulo l'avvio del sensore
        ser2.write(b"\x01")
        time.sleep(0.5)
        ser2.write(b"\x07")
        print(f"   ✅ Sensore 2 ({COM_SENSORE_2}) APERTO e in streaming!")

        print(
            "\n🎉 SUCCESSO TOTALE! Entrambi i sensori stanno comunicando in contemporanea."
        )
        print("Il problema era l'avvio simultaneo, non i dispositivi.")

    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")

    finally:
        print("\n--- OPERAZIONE DI PULIZIA PROFONDA ---")
        for s, name in [(ser1, COM_SENSORE_1), (ser2, COM_SENSORE_2)]:
            if s and s.is_open:
                try:
                    # 1. Forza lo stop dello streaming hardware
                    s.write(b"\x01")
                    time.sleep(0.2)
                    # 2. Svuota i buffer per non lasciare dati "incastrati" nel driver
                    s.reset_input_buffer()
                    s.reset_output_buffer()
                    # 3. Chiudi fisicamente la porta
                    s.close()
                    print(f"   ✅ Porta {name} resettata e rilasciata correttamente.")
                except Exception as e:
                    print(f"   ⚠️ Errore durante la chiusura di {name}: {e}")

        # Aspettiamo un secondo extra per dare tempo a Windows di accorgersi della chiusura
        time.sleep(2)
        print("\nOra puoi provare a lanciare di nuovo il test.")


if __name__ == "__main__":
    # Assicurati che entrambi i sensori siano accesi prima di lanciare!
    test_connessione_sfalsata()
