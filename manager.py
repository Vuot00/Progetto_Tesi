# manager.py
import threading
import time
from collections import deque
import streamlit as st

class HardwareManager:
    def __init__(self):
        # Dati ECG
        self.bpm_display = 0
        self.bpm_buffer = deque([70] * 10, maxlen=10)
        self.ecg_history = deque([0] * 500, maxlen=500)
        self.ecg_status = "🔴 In attesa..."
        
        # Dati IMU
        self.activity_level = 0
        self.imu_history = deque([0] * 500, maxlen=500)
        self.imu_status = "🔴 In attesa..."
        self.imu_offset = 0
        self._imu_initialized = False
        
        # Sincronizzazione e Stato Globale
        self.running = True
        self.data_lock = threading.Lock()
        
        # Watchdog timestamp
        self.ultimo_pacchetto_ecg = time.time()
        self.ultimo_pacchetto_imu = time.time()

# Il Singleton ufficiale di Streamlit per mantenere i dati vivi tra i refresh
@st.cache_resource
def get_manager():
    return HardwareManager()