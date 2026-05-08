import pandas as pd
import matplotlib.pyplot as plt
import os

# --- CONFIGURAZIONE ---
NOME_FILE_CSV = "dati_sessione.csv"

def main():
    print(f"Ricerca del file {NOME_FILE_CSV} in corso...")
    
    # 1. Controllo esistenza file
    if not os.path.isfile(NOME_FILE_CSV):
        print("Errore: Il file CSV non esiste. Assicurati di aver avviato la registrazione dalla Dashboard.")
        return

    # 2. Caricamento dei dati con Pandas
    # Le colonne del nostro CSV sono: ["Timestamp", "Sensore", "Valore_Primario", "Valore_Secondario"]
    try:
        df = pd.read_csv(NOME_FILE_CSV)
    except Exception as e:
        print(f"Errore durante la lettura del CSV: {e}")
        return

    if df.empty:
        print("Il file CSV è vuoto. Registra qualche dato prima di analizzarlo.")
        return

    print("Dati caricati con successo. Elaborazione in corso...")

    # 3. Separazione dei dati per sensore
    df_ecg = df[df['Sensore'] == 'ECG'].copy()
    df_imu = df[df['Sensore'] == 'IMU'].copy()

    # 4. Normalizzazione dell'asse del tempo (partiamo dal secondo 0)
    tempo_iniziale = df['Timestamp'].min()
    
    if not df_ecg.empty:
        df_ecg['Tempo_Relativo'] = df_ecg['Timestamp'] - tempo_iniziale
    if not df_imu.empty:
        df_imu['Tempo_Relativo'] = df_imu['Timestamp'] - tempo_iniziale

    # 5. Creazione del Grafico Accademico (2 sezioni, stesso asse X)
    # Impostiamo una dimensione bella larga, ideale per le pagine di una tesi
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # --- GRAFICO SUPERIORE: ECG (BPM) ---
    if not df_ecg.empty:
        # Valore_Secondario per l'ECG è il BPM (come definito in app.py)
        ax1.plot(df_ecg['Tempo_Relativo'], df_ecg['Valore_Secondario'], color='red', linewidth=2, label='Frequenza Cardiaca (BPM)')
        ax1.set_ylabel('BPM', fontsize=12, fontweight='bold')
        ax1.set_title('Risposta Cardiovascolare', fontsize=14)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='upper right')
    else:
        ax1.text(0.5, 0.5, 'Nessun dato ECG registrato', ha='center', va='center')

    # --- GRAFICO INFERIORE: IMU (Attività Motoria) ---
    if not df_imu.empty:
        # Valore_Primario per l'IMU è l'Activity Level
        ax2.fill_between(df_imu['Tempo_Relativo'], df_imu['Valore_Primario'], color='royalblue', alpha=0.5, label='Attività Fisica (IMU)')
        ax2.plot(df_imu['Tempo_Relativo'], df_imu['Valore_Primario'], color='darkblue', linewidth=1)
        ax2.set_ylabel('Intensità Movimento', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Tempo (Secondi dall\'inizio del test)', fontsize=12, fontweight='bold')
        ax2.set_title('Sforzo Fisico Misurato', fontsize=14)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper right')
    else:
        ax2.text(0.5, 0.5, 'Nessun dato IMU registrato', ha='center', va='center')

    # 6. Ottimizzazione layout e salvataggio
    plt.suptitle('Caso di Studio: Analisi Sincronizzata ECG - IMU', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Salva il grafico come immagine ad alta risoluzione (ottima per PDF/Word)
    nome_immagine = "risultato_caso_studio.png"
    plt.savefig(nome_immagine, dpi=300)
    print(f"\nGrafico salvato con successo come '{nome_immagine}'!")
    
    # Mostra la finestra interattiva
    plt.show()

if __name__ == "__main__":
    main()