import pandas as pd
import numpy as np
import joblib

from scipy.signal import find_peaks, butter, filtfilt
from scipy.interpolate import interp1d
from scipy.signal import welch
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix

NOME_FILE_CSV = "wesad_tutti.csv"
NOME_MODELLO = "modello_wesad.pkl"
FREQUENZA_WESAD = 700
FINESTRA_SECONDI = 60
STEP_SECONDI = 10
FEATURE_COLS = [
    "BPM",
    "RMSSD",
    "SDNN",
    "MeanRR",
    "LF_HF",
    "Activity_Mean",
    "Activity_Std",
]
SOGGETTI_ESCLUSI = {"S3", "S5", "S7", "S10", "S13", "S15", "S16"}


def bandpass_ecg(segnale, fs=700, low=0.5, high=40):
    b, a = butter(3, [low / (fs / 2), high / (fs / 2)], btype="band")
    return filtfilt(b, a, segnale)


def hrv_spettrale(rr_ms, fs_rr=4.0):
    if len(rr_ms) < 8:
        return 0.0, 0.0, 0.0
    t = np.cumsum(rr_ms) / 1000.0
    t -= t[0]
    f_interp = interp1d(t, rr_ms, kind="linear", fill_value="extrapolate")
    t_uniform = np.arange(0, t[-1], 1.0 / fs_rr)
    rr_uniform = f_interp(t_uniform)
    freqs, psd = welch(rr_uniform, fs=fs_rr, nperseg=min(len(rr_uniform), 256))
    lf = np.trapezoid(
        psd[(freqs >= 0.04) & (freqs < 0.15)], freqs[(freqs >= 0.04) & (freqs < 0.15)]
    )
    hf = np.trapezoid(
        psd[(freqs >= 0.15) & (freqs < 0.40)], freqs[(freqs >= 0.15) & (freqs < 0.40)]
    )
    lf_hf = lf / hf if hf > 0 else 0.0
    return lf, hf, lf_hf


def estrai_feature(finestra, fs=700, durata=60):
    ecg_raw = finestra["ECG_Raw"].values
    imu = finestra["IMU_Activity"].values

    try:
        ecg = bandpass_ecg(ecg_raw, fs)
    except Exception:
        ecg = ecg_raw

    soglia = np.mean(ecg) + 0.6 * np.std(ecg)
    picchi, _ = find_peaks(ecg, distance=int(fs * 0.4), height=soglia)

    if len(picchi) < 5:
        return None

    bpm = (len(picchi) / durata) * 60
    rr = np.diff(picchi) / fs * 1000
    rmssd = np.sqrt(np.mean(np.diff(rr) ** 2))
    sdnn = np.std(rr)
    mean_rr = np.mean(rr)
    _, _, lf_hf = hrv_spettrale(rr)
    activity_mean = np.mean(imu)
    activity_std = np.std(imu)

    return [bpm, rmssd, sdnn, mean_rr, lf_hf, activity_mean, activity_std]


def main():
    print("📊 Caricamento dati...")
    df = pd.read_csv(NOME_FILE_CSV)
    soggetti = [s for s in df["Soggetto"].unique() if s not in SOGGETTI_ESCLUSI]
    print(f"Soggetti usati: {soggetti}")

    dim_finestra = FREQUENZA_WESAD * FINESTRA_SECONDI
    dim_step = FREQUENZA_WESAD * STEP_SECONDI

    print("✂️ Estrazione feature per soggetto...")
    feature_per_soggetto = {}
    for soggetto in soggetti:
        df_s = df[df["Soggetto"] == soggetto].reset_index(drop=True)
        righe = []
        for i in range(0, len(df_s) - dim_finestra, dim_step):
            finestra = df_s.iloc[i : i + dim_finestra]
            label = finestra["Label"].mode()[0]
            feat = estrai_feature(finestra)
            if feat is not None:
                righe.append(feat + [label])
        feature_per_soggetto[soggetto] = pd.DataFrame(
            righe, columns=FEATURE_COLS + ["Label"]
        )
        print(f"  {soggetto}: {len(righe)} finestre")

    print("\n🧠 Addestramento con Leave-One-Subject-Out...")
    risultati = []
    for soggetto_test in soggetti:
        df_train = pd.concat(
            [feature_per_soggetto[s] for s in soggetti if s != soggetto_test]
        )
        df_test = feature_per_soggetto[soggetto_test]

        pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=8,
                        class_weight="balanced",
                        min_samples_leaf=3,
                        random_state=42,
                    ),
                ),
            ]
        )
        pipeline.fit(df_train[FEATURE_COLS], df_train["Label"])
        pred = pipeline.predict(df_test[FEATURE_COLS])
        acc = np.mean(pred == df_test["Label"])
        risultati.append(acc)

        cm = confusion_matrix(df_test["Label"], pred)
        print(
            f"  Test su {soggetto_test}: accuracy = {acc:.2f} | CM: {cm.diagonal()}/{cm.sum(axis=1)}"
        )

    print(
        f"\n📈 Accuracy media LOSO: {np.mean(risultati):.2f} ± {np.std(risultati):.2f}"
    )

    print("\n🏆 Addestramento modello finale su tutti i soggetti...")
    df_tutti = pd.concat(feature_per_soggetto.values())
    modello_finale = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    class_weight="balanced",
                    min_samples_leaf=3,
                    random_state=42,
                ),
            ),
        ]
    )
    modello_finale.fit(df_tutti[FEATURE_COLS], df_tutti["Label"])

    print("\n📊 Report sul training set completo:")
    print(
        classification_report(
            df_tutti["Label"],
            modello_finale.predict(df_tutti[FEATURE_COLS]),
            target_names=["Riposo", "Stress", "Divertimento"],
        )
    )

    joblib.dump(modello_finale, NOME_MODELLO)
    print(f"✅ Modello salvato come '{NOME_MODELLO}'")


if __name__ == "__main__":
    main()
