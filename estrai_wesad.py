import kagglehub
import pickle
import pandas as pd
import numpy as np
import os

NOME_OUTPUT_CSV = "wesad_tutti.csv"
SOGGETTI = ["S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10",
            "S11", "S13", "S14", "S15", "S16", "S17"]  # S12 mancante nel dataset

def estrai_soggetto(dataset_path, soggetto):
    for base in [os.path.join(dataset_path, "WESAD"), dataset_path]:
        path = os.path.join(base, soggetto, f"{soggetto}.pkl")
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                dati = pickle.load(f, encoding='latin1')

            ecg = dati['signal']['chest']['ECG'].flatten()
            acc = dati['signal']['chest']['ACC']
            imu = np.sqrt(acc[:, 0]**2 + acc[:, 1]**2 + acc[:, 2]**2)
            label = dati['label'].flatten()

            df = pd.DataFrame({
                'ECG_Raw': ecg,
                'IMU_Activity': imu,
                'Label_Originale': label,
                'Soggetto': soggetto
            })

            df = df[df['Label_Originale'].isin([1, 2, 3])].copy()
            df['Label'] = df['Label_Originale'].map({1: 0, 2: 1, 3: 2})
            df = df.drop(columns=['Label_Originale'])
            return df

    print(f"⚠️ Soggetto {soggetto} non trovato, saltato.")
    return None

def main():
    print("🌍 Download dataset WESAD...")
    dataset_path = kagglehub.dataset_download(
        "orvile/wesad-wearable-stress-affect-detection-dataset"
    )

    tutti = []
    for s in SOGGETTI:
        print(f"  Estrazione {s}...")
        df = estrai_soggetto(dataset_path, s)
        if df is not None:
            tutti.append(df)
            print(f"  ✅ {s}: {len(df)} campioni")

    df_finale = pd.concat(tutti, ignore_index=True)
    df_finale.to_csv(NOME_OUTPUT_CSV, index=False)
    print(f"\n🎉 Totale: {len(df_finale)} campioni da {len(tutti)} soggetti → {NOME_OUTPUT_CSV}")

if __name__ == "__main__":
    main()