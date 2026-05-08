# app.py
import streamlit as st
import time

# Importiamo dai nostri file separati
from manager import get_manager
from workers import start_threads_if_needed

# --- CONFIGURAZIONE PORTE ---
COM_IMU = "COM4"  # In uscita AAD4
COM_ECG = "COM5"  # In uscita 783C

def main():
    st.set_page_config(page_title="Dashboard Shimmer Live", layout="wide")
    st.title("🛰️ Monitoraggio Biometrico Live")

    # 1. Recupero il "Cervello" dei dati
    manager = get_manager()
    
    # 2. Controllo e avvio dei "Muscoli" hardware
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        start_threads_if_needed(manager, COM_IMU, COM_ECG)

    # 3. Snapshot sicuro dei dati (legge dal Manager)
    with manager.data_lock:
        ecg_data = list(manager.ecg_history)
        imu_data = list(manager.imu_history)
        bpm_current = manager.bpm_display
        activity_current = manager.activity_level
        ecg_status = manager.ecg_status
        imu_status = manager.imu_status

    # 4. Renderizzazione Grafica (Il "Viso")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Frequenza Cardiaca", f"{bpm_current} BPM", ecg_status)
        st.line_chart(ecg_data, height=300)
    with c2:
        st.metric("Attività Motoria", activity_current, imu_status)
        st.area_chart(imu_data, height=300)

    # 5. Loop visivo (Streamlit si aggiorna ogni 0.5s)
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()