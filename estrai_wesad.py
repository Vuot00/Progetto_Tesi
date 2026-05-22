# estrai_wesad.py
import kagglehub
import pickle
import pandas as pd
import numpy as np
import os

# --- CONFIGURAZIONE ---
NOME_OUTPUT_CSV = "wesad_pulito_S2.csv"
SOGGETTO = "S2" # Puoi cambiare questo valore per estrarre S3, S4, ecc.

def main():
    print("🌍 Connessione a Kaggle in corso per il dataset WESAD...")
    
    # 1. Download automatico tramite kagglehub
    try:
        dataset_path = kagglehub.dataset_download("orvile/wesad-wearable-stress-affect-detection-dataset")
        print(f"✅ Dataset trovato nella cache di Kaggle: {dataset_path}")
    except Exception as e:
        print(f"❌ Errore durante il download da Kaggle: {e}")
        return

    # 2. Costruzione dinamica del percorso al file .pkl
    # Controlliamo se esiste la sottocartella WESAD tipica degli archivi estratti
    percorso_con_cartella = os.path.join(dataset_path, "WESAD", SOGGETTO, f"{SOGGETTO}.pkl")
    percorso_senza_cartella = os.path.join(dataset_path, SOGGETTO, f"{SOGGETTO}.pkl")

    if os.path.isfile(percorso_con_cartella):
        percorso_file_wesad = percorso_con_cartella
    elif os.path.isfile(percorso_senza_cartella):
        percorso_file_wesad = percorso_senza_cartella
    else:
        print(f"❌ Impossibile trovare il file {SOGGETTO}.pkl all'interno del dataset scaricato.")
        return

    print(f"📂 Caricamento dei dati del soggetto dal file: {percorso_file_wesad}")

    # 3. Lettura del file Pickle (WESAD usa la codifica latin1)
    with open(percorso_file_wesad, 'rb') as file:
        dati_wesad = pickle.load(file, encoding='latin1')

    print("✅ File caricato. Estrazione dei sensori Chest (ECG + IMU)...")

    # 4. Navigazione nel dizionario WESAD
    ecg_grezzo = dati_wesad['signal']['chest']['ECG'].flatten()
    
    acc_x = dati_wesad['signal']['chest']['ACC'][:, 0]
    acc_y = dati_wesad['signal']['chest']['ACC'][:, 1]
    acc_z = dati_wesad['signal']['chest']['ACC'][:, 2]
    imu_magnitudo = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)

    etichette = dati_wesad['label'].flatten()

    # 5. Creazione del DataFrame Pandas
    print("📊 Creazione della tabella dati...")
    df = pd.DataFrame({
        'ECG_Raw': ecg_grezzo,
        'IMU_Activity': imu_magnitudo,
        'Label_Originale': etichette
    })

    # 6. Filtraggio delle Etichette (Teniamo Riposo, Stress e Divertimento)
    print("✂️ Pulizia dei dati (Rimozione transizioni e fasi non necessarie)...")
    df_filtrato = df[df['Label_Originale'].isin([1, 2, 3])].copy()
    
    # Rinominiamo le etichette: 0=Riposo, 1=Stress Cognitivo, 2=Divertimento
    df_filtrato['Label'] = df_filtrato['Label_Originale'].map({1: 0, 2: 1, 3: 2})
    df_filtrato = df_filtrato.drop(columns=['Label_Originale'])

    # 7. Salvataggio su CSV
    print(f"💾 Salvataggio in corso su {NOME_OUTPUT_CSV}...")
    df_filtrato.to_csv(NOME_OUTPUT_CSV, index=False)
    
    print(f"🎉 Estrazione completata! Hai isolato {len(df_filtrato)} campioni di puro ECG e IMU per il soggetto {SOGGETTO}.")

if __name__ == "__main__":
    main()