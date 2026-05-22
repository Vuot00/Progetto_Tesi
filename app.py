import streamlit as st
import time
import csv
import os
import joblib 
import pandas as pd
import numpy as np # Necessario per i calcoli matematici dell'HRV

# Importiamo dai nostri file separati
from manager import get_manager
from workers import start_threads_if_needed

# --- CONFIGURAZIONE PORTE E MODELLO ---
COM_IMU = "COM4"  
COM_ECG = "COM5"  
NOME_FILE_CSV = "dati_sessione.csv"
NOME_MODELLO = "modello_wesad.pkl" 

# --- CARICAMENTO MODELLO ML ---
@st.cache_resource
def carica_modello_ia():
    try:
        modello = joblib.load(NOME_MODELLO)
        return modello
    except Exception as e:
        st.error(f"Modello non trovato o errore di caricamento: {e}")
        return None

def main():
    st.set_page_config(page_title="Dashboard Shimmer Live", layout="wide")
    st.title("🧠 Intelligenza Artificiale & Analisi dello Stress")

    manager = get_manager()
    modello_ia = carica_modello_ia()
    
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        start_threads_if_needed(manager, COM_IMU, COM_ECG)

    # --- ZONA CONTROLLI ---
    c_header1, c_header2 = st.columns([3, 1])
    with c_header2:
        registra = st.toggle("🔴 Registra Dati CSV")

    # --- GESTIONE SCRITTURA CSV ASINCRONA ---
    if registra:
        manager.is_recording = True
        if not os.path.isfile(NOME_FILE_CSV):
            with open(NOME_FILE_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Sensore", "Valore_Primario", "Valore_Secondario", "Stato_IA"])

        with manager.data_lock:
            dati_copia = list(manager.dati_da_salvare)
            manager.dati_da_salvare.clear()
        
        if dati_copia:
            with open(NOME_FILE_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(dati_copia)
    else:
        manager.is_recording = False
        with manager.data_lock:
            manager.dati_da_salvare.clear()

    # --- ESTRAZIONE DATI ---
    with manager.data_lock:
        ecg_data = list(manager.ecg_history)
        imu_data = list(manager.imu_history)
        bpm_current = manager.bpm_display
        activity_current = manager.activity_level
        ecg_status = manager.ecg_status
        imu_status = manager.imu_status
        rr_list = list(manager.rr_intervals) # Estrazione tempi battiti

    # --- CALCOLO HRV (RMSSD) IN TEMPO REALE ---
    if len(rr_list) > 1:
        diff_rr = np.diff(rr_list)
        rmssd_current = int(np.sqrt(np.mean(diff_rr**2)) * 1000)
    else:
        rmssd_current = 0

    # --- INFERENZA MACHINE LEARNING EMOZIONALE E FISICA ---
    if modello_ia is not None and manager.ecg_status == "✅ ECG Connesso" and manager.imu_status == "✅ IMU Connesso":
        
        # IL GATEKEEPER FISICO
        # Se il movimento è molto alto, bypassiamo l'IA e dichiariamo lo sforzo fisico
        if activity_current > 150: # Puoi regolare questa soglia (es. 100 o 200) in base ai tuoi dati
            manager.stato_fisiologico = "🏃 IN MOVIMENTO (Analisi Emozioni Sospesa)"
            
        else:
            # Se l'utente è fermo, lasciamo parlare l'Intelligenza Artificiale
            feature_attuali = pd.DataFrame(
                [[bpm_current, rmssd_current, activity_current]], 
                columns=['BPM', 'RMSSD', 'Activity']
            )
            
            predizione = modello_ia.predict(feature_attuali)[0]
            
            if predizione == 0:
                manager.stato_fisiologico = "🟢 RIPOSO (Baseline)"
            elif predizione == 1:
                manager.stato_fisiologico = "🔴 STRESS COGNITIVO RILEVATO"
            elif predizione == 2:
                manager.stato_fisiologico = "🎉 DIVERTIMENTO / AMUSEMENT"
    else:
        manager.stato_fisiologico = "⏳ Attesa Dati..."

    # --- RENDERIZZAZIONE GRAFICA ---
    
    st.subheader(f"Stato Mentale/Fisico (AI): {manager.stato_fisiologico}")
    st.markdown("---")

    # NUOVO LAYOUT A 3 COLONNE!
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Frequenza Cardiaca", f"{bpm_current} BPM", ecg_status)
    with c2:
        # Mostriamo l'HRV. Più è alto, più si è rilassati.
        st.metric("Variabilità Cardiaca (HRV)", f"{rmssd_current} ms", "RMSSD")
    with c3:
        st.metric("Attività Motoria", activity_current, imu_status)

    # Grafici sottostanti
    cg1, cg2 = st.columns(2)
    with cg1:
        st.line_chart(ecg_data, height=300)
    with cg2:
        st.area_chart(imu_data, height=300)

    # Refresh
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()