# addestramento_wesad.py
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

# --- CONFIGURAZIONE ---
NOME_FILE_CSV = "wesad_pulito_S2.csv"
NOME_MODELLO = "modello_wesad.pkl"
FREQUENZA_WESAD = 700  # Hz (campionamenti al secondo)
FINESTRA_SECONDI = 3   # Analizziamo i dati a blocchi di 3 secondi

def main():
    print(f"🚀 Avvio pipeline di Machine Learning sul dataset WESAD...")
    
    if not os.path.isfile(NOME_FILE_CSV):
        print(f"❌ Errore: File {NOME_FILE_CSV} non trovato. Attendi la fine dell'estrazione.")
        return

    print("📊 1. Caricamento dei dati grezzi in memoria...")
    df = pd.read_csv(NOME_FILE_CSV)
    
    # Calcoliamo quanti campioni ci sono in una finestra di 3 secondi
    dimensione_finestra = FREQUENZA_WESAD * FINESTRA_SECONDI
    
    feature_estratte = []
    
    print("✂️ 2. Estrazione delle Feature (Calcolo BPM e Movimento ogni 3 secondi)...")
    # Scorriamo il dataset a "salti" di 3 secondi
    for i in range(0, len(df), dimensione_finestra):
        finestra = df.iloc[i : i + dimensione_finestra]
        
        # Scartiamo l'ultima finestra se è incompleta
        if len(finestra) < dimensione_finestra:
            break
            
        # --- A. Estrazione Attività Motoria (IMU) ---
        # Calcoliamo la deviazione standard del movimento (quanto è "agitato" il segnale)
        activity = np.std(finestra['IMU_Activity']) * 100 # Moltiplicato per scalarlo a valori interi simili allo Shimmer
        
        # --- B. Estrazione Frequenza Cardiaca e HRV ---
        ecg_raw = finestra['ECG_Raw'].values
        picchi, _ = find_peaks(ecg_raw, distance=200, height=np.mean(ecg_raw) + np.std(ecg_raw))
        
        if len(picchi) < 3: # Servono almeno 3 picchi per calcolare la variabilità
            continue
            
        bpm = (len(picchi) / FINESTRA_SECONDI) * 60
        
        # NUOVO: Calcolo HRV (RMSSD)
        # 1. Troviamo la distanza in secondi tra ogni battito
        rr_intervals = np.diff(picchi) / FREQUENZA_WESAD 
        # 2. Calcoliamo la differenza tra battiti successivi al quadrato, facciamo la media e la radice
        rmssd = np.sqrt(np.mean(np.diff(rr_intervals)**2)) * 1000 # *1000 per averlo in millisecondi
        
        # --- C. Etichetta ---
        label = finestra['Label'].mode()[0]
        
        # Salviamo i risultati (aggiungiamo rmssd all'array)
        feature_estratte.append([bpm, rmssd, activity, label])

    # 3. Creazione del Dataset Finale per il Modello
    df_features = pd.DataFrame(feature_estratte, columns=['BPM', 'RMSSD', 'Activity', 'Label'])
    print(f"✅ Feature estratte con successo! Create {len(df_features)} finestre temporali validabili.")
    
    # 4. Addestramento dell'Intelligenza Artificiale
    print("🧠 3. Addestramento del Classificatore (Random Forest)...")
    X = df_features[['BPM', 'RMSSD', 'Activity']]
    y = df_features['Label']
    
    # Dividiamo i dati: 80% studio, 20% esame
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Inizializziamo il modello limitando la profondità per evitare l'overfitting
    modello = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    modello.fit(X_train, y_train)
    
    # 5. Valutazione Accademica
    print("\n📈 4. Risultati della Classificazione (Metrics):")
    predizioni = modello.predict(X_test)
    print(classification_report(y_test, predizioni, target_names=['Riposo', 'Stress/Cognitivo', 'Divertimento']))
    
    # 6. Salvataggio
    joblib.dump(modello, NOME_MODELLO)
    print(f"\n🏆 Modello validato e salvato come '{NOME_MODELLO}'!")
    print("Ora puoi riaprire la dashboard Streamlit. L'errore rosso sarà sparito!")

if __name__ == "__main__":
    main()