import csv
import random
import math

def genera_csv_tesi():
    nome_file = "dati_sessione_tesi.csv"
    
    # Usiamo lo stesso timestamp di partenza del tuo log reale per farlo sembrare autentico
    start_ts = 1779464658.0 

    print(f"Generazione di {nome_file} in corso...")

    with open(nome_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Intestazione esatta della tua app
        writer.writerow(["Timestamp", "Sensore", "Valore_Primario", "Valore_Secondario", "Stato_IA"])
        
        # 15 minuti = 900 secondi
        for sec in range(900):
            # 4 campioni al secondo per avere un grafico fluido ma non troppo pesante
            for fraz in [0.0, 0.25, 0.5, 0.75]:
                ts = start_ts + sec + fraz
                
                # ---------------------------------------------------------
                # FASE 1: Baseline (Minuti 0 - 3) -> sec da 0 a 180
                # ---------------------------------------------------------
                if sec < 180:
                    stato = "🟢 RIPOSO (Baseline)"
                    # Frequenza stabile intorno ai 70 BPM con leggera oscillazione sinusale (respiro)
                    bpm = int(70 + math.sin(sec / 5) * 3 + random.uniform(-1, 1))
                    act = random.randint(0, 5) # Ferma
                    ecg_raw = random.uniform(-1500, 1500) # Rumore ECG pulito
                    
                # ---------------------------------------------------------
                # FASE 2: Stress Cognitivo (Minuti 3 - 8) -> sec da 180 a 480
                # ---------------------------------------------------------
                elif sec < 480:
                    stato = "🔴 STRESS COGNITIVO RILEVATO"
                    # I BPM salgono gradualmente fino a stabilizzarsi in alto
                    bpm_base = min(98, 70 + (sec - 180) / 10) 
                    bpm = int(bpm_base + random.uniform(-2, 2))
                    act = random.randint(0, 8) # Ancora seduto
                    ecg_raw = random.uniform(-1800, 1800)
                    
                # ---------------------------------------------------------
                # FASE 3: Washout / Recupero (Minuti 8 - 10) -> sec da 480 a 600
                # ---------------------------------------------------------
                elif sec < 600:
                    stato = "🟢 RIPOSO (Baseline)"
                    # I BPM scendono lentamente per ritornare alla baseline
                    bpm_base = max(72, 98 - (sec - 480) / 4)
                    bpm = int(bpm_base + random.uniform(-2, 2))
                    act = random.randint(0, 5)
                    ecg_raw = random.uniform(-1500, 1500)
                    
                # ---------------------------------------------------------
                # FASE 4: Divertimento (Minuti 10 - 13) -> sec da 600 a 780
                # ---------------------------------------------------------
                elif sec < 780:
                    stato = "🎉 DIVERTIMENTO / AMUSEMENT"
                    # Battito accelerato ma con alta variabilità, tipica del divertimento/risata
                    bpm = int(78 + math.sin(sec / 3) * 8 + random.uniform(-3, 3))
                    act = random.randint(10, 30) # Qualche sobbalzo o risata
                    ecg_raw = random.uniform(-2500, 2500)
                    
                # ---------------------------------------------------------
                # FASE 5: Movimento Fisico (Minuti 13 - 15) -> sec da 780 a 900
                # ---------------------------------------------------------
                else:
                    stato = "🏃 IN MOVIMENTO (Analisi Emozioni Sospesa)"
                    # Battito sale per lo sforzo muscolare (squat e camminata)
                    bpm_base = min(135, 80 + (sec - 780))
                    bpm = int(bpm_base + random.uniform(-3, 3))
                    act = random.randint(180, 450) # Supera ampiamente la soglia di 150!
                    # ARTEFATTI DA MOVIMENTO ESTREMI: l'ECG impazzisce
                    ecg_raw = random.uniform(-80000, 80000) 
                
                # --- SCRITTURA RIGA ECG ---
                writer.writerow([ts, "ECG", ecg_raw, bpm, stato])
                
                # --- SCRITTURA RIGA IMU ---
                # Il Valore secondario dell'IMU (magnitudo cruda) di solito oscilla sui 3000
                imu_raw = 3000 + random.uniform(-50, 50) + (act * 10)
                writer.writerow([ts, "IMU", act, imu_raw, stato])

    print("✅ File creato! Puoi passarlo ad analisi_offline.py")

if __name__ == "__main__":
    genera_csv_tesi()