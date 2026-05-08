import streamlit as st
import time
import csv
import os

# Importiamo dai nostri file separati
from manager import get_manager
from workers import start_threads_if_needed

# --- CONFIGURAZIONE PORTE ---
COM_IMU = "COM5"  
COM_ECG = "COM8"  
NOME_FILE_CSV = "dati_sessione.csv"

def main():
    st.set_page_config(page_title="Dashboard Shimmer Live", layout="wide")
    st.title("🛰️ Monitoraggio Biometrico Live")

    manager = get_manager()
    
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
        
        # Crea intestazione se il file non esiste
        if not os.path.isfile(NOME_FILE_CSV):
            with open(NOME_FILE_CSV, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Sensore", "Valore_Primario", "Valore_Secondario"])

        # Svuota il secchio temporaneo in modo sicuro
        with manager.data_lock:
            dati_copia = list(manager.dati_da_salvare)
            manager.dati_da_salvare.clear()
        
        # Scrive sul disco
        if dati_copia:
            with open(NOME_FILE_CSV, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(dati_copia)
    else:
        manager.is_recording = False
        with manager.data_lock:
            manager.dati_da_salvare.clear() # Pulisce la coda quando è fermo

    # --- ESTRAZIONE DATI PER GRAFICI ---
    with manager.data_lock:
        ecg_data = list(manager.ecg_history)
        imu_data = list(manager.imu_history)
        bpm_current = manager.bpm_display
        activity_current = manager.activity_level
        ecg_status = manager.ecg_status
        imu_status = manager.imu_status

    # --- RENDERIZZAZIONE GRAFICA ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Frequenza Cardiaca", f"{bpm_current} BPM", ecg_status)
        st.line_chart(ecg_data, height=300)
    with c2:
        st.metric("Attività Motoria", activity_current, imu_status)
        st.area_chart(imu_data, height=300)

    # Refresh
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()