import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.patches as mpatches

# --- CONFIGURAZIONE ---
NOME_FILE_CSV = "dati_sessione.csv"

def main():
    print(f"Ricerca del file {NOME_FILE_CSV} in corso...")
    
    if not os.path.isfile(NOME_FILE_CSV):
        print("❌ Errore: Il file CSV non esiste. Avvia prima una registrazione dalla Dashboard.")
        return

    # 1. Caricamento Dati
    try:
        df = pd.read_csv(NOME_FILE_CSV)
    except Exception as e:
        print(f"❌ Errore durante la lettura del CSV: {e}")
        return

    if df.empty:
        print("⚠️ Il file CSV è vuoto. Registra qualche dato prima di analizzarlo.")
        return

    print("✅ Dati caricati. Generazione del grafico emozionale in corso...")

    # Rimuoviamo eventuali righe corrotte
    df = df.dropna(subset=['Timestamp', 'Sensore'])

    # 2. Separazione dei sensori
    df_ecg = df[df['Sensore'] == 'ECG'].copy()
    df_imu = df[df['Sensore'] == 'IMU'].copy()

    # 3. Normalizzazione dell'asse X (partiamo dal secondo 0)
    tempo_iniziale = df['Timestamp'].min()
    if not df_ecg.empty:
        df_ecg['Tempo_Relativo'] = df_ecg['Timestamp'] - tempo_iniziale
    if not df_imu.empty:
        df_imu['Tempo_Relativo'] = df_imu['Timestamp'] - tempo_iniziale

    # 4. Creazione del Grafico Accademico (2 Sezioni)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # --- GRAFICO SUPERIORE: ECG (BPM) ---
    if not df_ecg.empty:
        # Disegniamo la linea rossa dei BPM
        ax1.plot(df_ecg['Tempo_Relativo'], df_ecg['Valore_Secondario'], color='red', linewidth=2, label='Frequenza Cardiaca (BPM)')
        ax1.set_ylabel('BPM', fontsize=12, fontweight='bold')
        ax1.set_title('Risposta Cardiovascolare & Stati Emotivi', fontsize=14)
        ax1.grid(True, linestyle='--', alpha=0.7)

        # --- LA MAGIA DELL'IA (Gestione 3 Stati + Movimento) ---
        if 'Stato_IA' in df_ecg.columns:
            # Creiamo le maschere booleane per i diversi stati
            is_stress = df_ecg['Stato_IA'].astype(str).str.contains('STRESS', na=False, case=False)
            is_amusement = df_ecg['Stato_IA'].astype(str).str.contains('DIVERTIMENTO', na=False, case=False)
            is_movement = df_ecg['Stato_IA'].astype(str).str.contains('MOVIMENTO', na=False, case=False)

            # Riempiamo gli sfondi con colori semantici
            ax1.fill_between(df_ecg['Tempo_Relativo'], 0, 1, where=is_stress, 
                             color='orange', alpha=0.3, transform=ax1.get_xaxis_transform(),
                             label='Stress Cognitivo')
            ax1.fill_between(df_ecg['Tempo_Relativo'], 0, 1, where=is_amusement, 
                             color='lightgreen', alpha=0.4, transform=ax1.get_xaxis_transform(),
                             label='Divertimento / Relax')
            ax1.fill_between(df_ecg['Tempo_Relativo'], 0, 1, where=is_movement, 
                             color='lightgray', alpha=0.5, transform=ax1.get_xaxis_transform(),
                             label='In Movimento (IA Sospesa)')
            
        ax1.legend(loc='upper right')

    # --- GRAFICO INFERIORE: IMU (Attività Motoria) ---
    if not df_imu.empty:
        # Disegniamo l'area blu del movimento
        ax2.fill_between(df_imu['Tempo_Relativo'], df_imu['Valore_Primario'], color='royalblue', alpha=0.5, label='Attività Fisica (IMU)')
        ax2.plot(df_imu['Tempo_Relativo'], df_imu['Valore_Primario'], color='darkblue', linewidth=1)
        ax2.set_ylabel('Intensità Movimento', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Tempo (Secondi dall\'inizio del test)', fontsize=12, fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.7)

        # Coloriamo lo sfondo anche sotto per allineamento visivo
        if 'Stato_IA' in df_imu.columns:
            is_stress_imu = df_imu['Stato_IA'].astype(str).str.contains('STRESS', na=False, case=False)
            is_amusement_imu = df_imu['Stato_IA'].astype(str).str.contains('DIVERTIMENTO', na=False, case=False)
            is_movement_imu = df_imu['Stato_IA'].astype(str).str.contains('MOVIMENTO', na=False, case=False)

            ax2.fill_between(df_imu['Tempo_Relativo'], 0, 1, where=is_stress_imu, color='orange', alpha=0.3, transform=ax2.get_xaxis_transform())
            ax2.fill_between(df_imu['Tempo_Relativo'], 0, 1, where=is_amusement_imu, color='lightgreen', alpha=0.4, transform=ax2.get_xaxis_transform())
            ax2.fill_between(df_imu['Tempo_Relativo'], 0, 1, where=is_movement_imu, color='lightgray', alpha=0.5, transform=ax2.get_xaxis_transform())

        ax2.legend(loc='upper right')

    # 5. Ottimizzazione e Salvataggio
    plt.suptitle('Analisi Emozionale WESAD: Stress Cognitivo vs Rilassamento', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    nome_immagine = "risultato_emozioni_validazione.png"
    plt.savefig(nome_immagine, dpi=300)
    print(f"🎉 Grafico salvato con successo come '{nome_immagine}'!")
    
    # Mostra l'immagine a schermo
    plt.show()

if __name__ == "__main__":
    main()