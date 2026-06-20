import numpy as np
import pandas as pd
from src.config import (
    DATE_START, DATE_END, FREQ, PROCESSED_DATA_FILE, DUMMY_DATES
)


def _idx():
    return pd.date_range(start=DATE_START, end=DATE_END, freq=FREQ)


def nettoyer_oil(oil):
    oil = oil.resample("MS").ffill()
    idx = _idx()
    oil = oil.reindex(idx).ffill()
    return oil


def _tendance(n, pente=0.15, volatilite=2.0, seed=None):
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(pente, volatilite, n))


def generer_synthetique(oil_reel, cpi_reel=None, seed=42):
    idx = _idx()
    rng_exr = np.random.default_rng(seed)
    rng_m2 = np.random.default_rng(seed + 10)
    rng_inf = np.random.default_rng(seed + 20)
    n = len(idx)
    annee = np.arange(n) / 12

    # Calibrer EXR: dépréciation MGA/USD ~5-8% par an
    exr_trend = 6000 + annee * 150
    exr_rw = np.cumsum(rng_exr.normal(0, 12, n))
    exr = np.maximum(exr_trend + exr_rw, 1000)

    # Calibrer M2: croissance nominale ~12-15% par an (indépendant de EXR)
    m2_trend = 800 + annee * 8
    m2_rw = np.cumsum(rng_m2.normal(0, 3, n))
    m2 = np.maximum(m2_trend + m2_rw, 100)

    # INF avec tendance haussière
    inf = 90 + annee * 0.3 + np.cumsum(rng_inf.normal(0, 1.5, n))
    inf = np.abs(inf) + 80

    # Remplacer INF réel si disponible (à partir de 2016)
    if cpi_reel is not None and len(cpi_reel) > 0:
        cpi_reel = cpi_reel[cpi_reel.index <= idx[-1]]
        first_real_date = cpi_reel.index[0]
        mask_reel = idx >= first_real_date
        inf[mask_reel] = cpi_reel.values

    return {"EXR": exr, "M2": m2, "INF": inf}


def ajouter_dummies(df):
    for name, (start, end) in DUMMY_DATES.items():
        df[name] = ((df.index >= start) & (df.index <= end)).astype(float)
    return df


def assembler_dataset(oil, synthetique):
    idx = _idx()
    df = pd.DataFrame(index=idx)
    df["OIL"] = oil.values
    df["EXR"] = synthetique["EXR"]
    df["M2"] = synthetique["M2"]
    df["INF"] = synthetique["INF"]
    df = ajouter_dummies(df)
    df.columns.name = "Variable"
    df.index.name = "Date"
    return df


def nettoyer_avec_reelles():
    """Utilise les données réelles (Banque Mondiale, INSTAT) avec fallback synthétique."""
    from src.collecte_reelle import generer_dataset_final

    print("[Nettoyage] Collecte des données réelles...")
    df = generer_dataset_final(ajouter_dummies=True)

    dummies = [c for c in df.columns if c.startswith("D")]
    print(f"[Nettoyage] Dataset sauvegardé: {PROCESSED_DATA_FILE}")
    print(f"[Nettoyage] Shape: {df.shape}, {df.index[0].date()} - {df.index[-1].date()}")
    print(f"[Nettoyage] Variables: {[c for c in df.columns if not c.startswith('D')]}")
    print(f"[Nettoyage] Muettes: {dummies}")

    df.to_csv(PROCESSED_DATA_FILE)
    return df


def nettoyer_et_sauvegarder(donnees=None):
    """Point d'entrée principal : données réelles d'abord, fallback synthétique."""
    try:
        return nettoyer_avec_reelles()
    except Exception as e:
        print(f"[Nettoyage] Échec des données réelles ({e}), fallback synthétique.")
        if donnees is None:
            from src.collecte import collecter_cpi, collecter_oil
            donnees = {"cpi": collecter_cpi(), "oil": collecter_oil()}
        oil = nettoyer_oil(donnees["oil"])
        cpi_reel = donnees["cpi"]
        syn = generer_synthetique(oil, cpi_reel)
        df = assembler_dataset(oil, syn)

        dummies = [c for c in df.columns if c.startswith("D")]
        print(f"[Nettoyage] Dataset sauvegardé: {PROCESSED_DATA_FILE}")
        print(f"[Nettoyage] Shape: {df.shape}, {df.index[0].date()} - {df.index[-1].date()}")
        print(f"[Nettoyage] Variables: {[c for c in df.columns if not c.startswith('D')]}")
        print(f"[Nettoyage] Muettes: {dummies}")

        df.to_csv(PROCESSED_DATA_FILE)
        return df


if __name__ == "__main__":
    nettoyer_et_sauvegarder()
