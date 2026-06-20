"""
Module de collecte de données réelles depuis des APIs gratuites.
Sources :
- Banque Mondiale API (https://api.worldbank.org/v2/)
- IMF SDMX API (https://sdmxcentral.imf.org/)
- INSTAT Madagascar (fichier Excel local)

Aucune clé API requise pour la Banque Mondiale.
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = CURRENT_DIR / "data" / "raw"
DATA_EXTERNAL = CURRENT_DIR / "data" / "external"


def fetch_exr_wb():
    """Taux de change MGA/USD - Banque Mondiale (annuel)"""
    url = "https://api.worldbank.org/v2/country/MG/indicator/PA.NUS.FCRF?format=json&date=2000:2025"
    r = requests.get(url, timeout=30)
    data = r.json()
    rows = [(int(x["date"]), float(x["value"])) for x in data[1] if x.get("value")]
    df = pd.DataFrame(rows, columns=["year", "EXR"]).set_index("year")
    df.index.name = "year"
    return df


def fetch_cpi_wb():
    """IPC niveau - Banque Mondiale (annuel, base 2010=100)"""
    url = "https://api.worldbank.org/v2/country/MG/indicator/FP.CPI.TOTL?format=json&date=2000:2025"
    r = requests.get(url, timeout=30)
    data = r.json()
    rows = [(int(x["date"]), float(x["value"])) for x in data[1] if x.get("value")]
    df = pd.DataFrame(rows, columns=["year", "CPI_WB"]).set_index("year")
    df.index.name = "year"
    return df


def fetch_m2_wb():
    """Masse monétaire M2 (niveau, LCU) - Banque Mondiale (annuel)"""
    url = "https://api.worldbank.org/v2/country/MG/indicator/FM.LBL.BMNY.CN?format=json&date=2000:2025"
    r = requests.get(url, timeout=30)
    data = r.json()
    rows = [(int(x["date"]), float(x["value"])) for x in data[1] if x.get("value")]
    df = pd.DataFrame(rows, columns=["year", "M2_WB"]).set_index("year")
    df.index.name = "year"
    return df


def annual_to_monthly(df_annual, start="2000-01-01", end="2025-01-01"):
    """Convertit une série annuelle en mensuelle par interpolation linéaire."""
    idx_monthly = pd.date_range(start=start, end=end, freq="MS")
    col_name = df_annual.columns[0]
    # Créer une série avec les valeurs annuelles au 1er juillet
    dates_annual = pd.to_datetime([f"{y}-07-01" for y in df_annual.index])
    ser_annual = pd.Series(df_annual[col_name].values, index=dates_annual)
    # Interpoler + remplir les bords
    ser_monthly = (ser_annual.reindex(idx_monthly).interpolate(method="linear").bfill().ffill())
    return ser_monthly


def fetch_oil_brent():
    """Prix du pétrole Brent depuis le fichier local Banque Mondiale Pink Sheet."""
    fp = DATA_EXTERNAL / "oil-prices-world-bank-pink-sheets.xlsx"
    if not fp.exists():
        print("[WARN] Fichier pétrole non trouvé, données synthétiques utilisées.")
        return None
    df = pd.read_excel(fp, header=None)
    valeurs = df.iloc[2:, 3].astype(float)
    dates = pd.to_datetime(df.iloc[2:, 1], errors="coerce")
    oil = pd.Series(valeurs.values, index=dates, name="OIL")
    oil = oil[oil.index.notna()].sort_index()
    # Mensuel
    oil = oil.resample("MS").ffill()
    idx = pd.date_range(start="2000-01-01", end="2025-01-01", freq="MS")
    oil = oil.reindex(idx).ffill()
    return oil


def fetch_cpi_instat():
    """IPC réel depuis le fichier INSTAT Excel."""
    fp = DATA_RAW / "INSTAT_NIPC-Mars-2026.xlsx"
    if not fp.exists():
        print("[WARN] Fichier CPI INSTAT non trouvé.")
        return None
    df = pd.read_excel(fp, header=None)
    valeurs = df.iloc[13, 2:].astype(float)
    dates = pd.to_datetime(df.iloc[12, 2:], errors="coerce")
    cpi = pd.Series(valeurs.values, index=dates, name="INF_INSTAT")
    cpi = cpi[cpi.index.notna()].sort_index()
    return cpi


def fetch_exr_fred(api_key=None):
    """Taux de change mensuel MGA/USD depuis FRED API (si clé disponible)."""
    if api_key is None:
        import os
        api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=EXRAUSMMM&api_key={api_key}"
        f"&file_type=json&observation_start=2000-01-01&observation_end=2025-01-01"
        f"&sort_order=asc"
    )
    r = requests.get(url, timeout=30)
    data = r.json()
    if "observations" not in data:
        return None
    rows = []
    for obs in data["observations"]:
        if obs["value"] != ".":
            rows.append((obs["date"], float(obs["value"])))
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["date", "EXR_FRED"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df["EXR_FRED"]


def collecter_donnees_reelles():
    """
    Collecte toutes les données réelles disponibles et retourne un DataFrame
    mensuel de 2000-01 à 2025-01 avec les séries les plus complètes possibles.
    """
    idx = pd.date_range(start="2000-01-01", end="2025-01-01", freq="MS")
    result = pd.DataFrame(index=idx)

    # 1. Pétrole Brent (fichier local)
    oil = fetch_oil_brent()
    if oil is not None:
        result["OIL"] = oil

    # 2. CPI INSTAT (local, haute fréquence mais partiel)
    cpi_instat = fetch_cpi_instat()
    if cpi_instat is not None:
        cpi_instat = cpi_instat[cpi_instat.index <= idx[-1]]
        result["INF_INSTAT"] = cpi_instat

    # 3. Banque Mondiale - EXR (annuel -> mensuel par interpolation)
    try:
        exr_annual = fetch_exr_wb()
        if not exr_annual.empty:
            result["EXR"] = annual_to_monthly(exr_annual)
    except Exception as e:
        print(f"[WARN] Échec EXR Banque Mondiale: {e}")

    # 4. Banque Mondiale - M2 (annuel -> mensuel)
    try:
        m2_annual = fetch_m2_wb()
        if not m2_annual.empty:
            result["M2"] = annual_to_monthly(m2_annual)
    except Exception as e:
        print(f"[WARN] Échec M2 Banque Mondiale: {e}")

    # 5. Banque Mondiale - CPI (annuel -> mensuel, pour compléter INSTAT si besoin)
    try:
        cpi_wb = fetch_cpi_wb()
        if not cpi_wb.empty:
            result["CPI_WB"] = annual_to_monthly(cpi_wb)
    except Exception as e:
        print(f"[WARN] Échec CPI Banque Mondiale: {e}")

    # 6. FRED API - EXR mensuel (si clé disponible)
    try:
        exr_fred = fetch_exr_fred()
        if exr_fred is not None:
            result["EXR_FRED"] = exr_fred
            # FRED est mensuel donc plus précis, remplacer EXR
            result["EXR"] = exr_fred
    except Exception as e:
        print(f"[WARN] FRED EXR non disponible: {e}")

    return result


def generer_dataset_final(ajouter_dummies=True):
    """
    Génère le dataset final avec les variables OIL, EXR, M2, INF.
    Utilise les données réelles disponibles, complète avec synthétique
    si nécessaire, et ajoute les dummies structurelles.
    """
    idx = pd.date_range(start="2000-01-01", end="2025-01-01", freq="MS")
    df = pd.DataFrame(index=idx)

    # Collecter données réelles
    reelles = collecter_donnees_reelles()

    # --- OIL ---
    if "OIL" in reelles.columns and reelles["OIL"].notna().sum() > 0:
        df["OIL"] = reelles["OIL"]
    else:
        print("[WARN] OIL non disponible, données synthétiques utilisées.")
        np.random.seed(0)
        df["OIL"] = 50 + 30 * np.sin(np.arange(len(idx)) / 24) + np.cumsum(np.random.normal(0, 2, len(idx)))

    # --- EXR ---
    if "EXR" in reelles.columns and reelles["EXR"].notna().sum() > 0:
        df["EXR"] = reelles["EXR"]
    else:
        print("[WARN] EXR non disponible, données synthétiques utilisées.")
        rng = np.random.default_rng(42)
        annee = np.arange(len(idx)) / 12
        exr_trend = 6000 + annee * 150
        exr_rw = np.cumsum(rng.normal(0, 12, len(idx)))
        df["EXR"] = np.maximum(exr_trend + exr_rw, 1000)

    # --- M2 ---
    if "M2" in reelles.columns and reelles["M2"].notna().sum() > 0:
        df["M2"] = reelles["M2"]
    else:
        print("[WARN] M2 non disponible, données synthétiques utilisées.")
        rng = np.random.default_rng(52)
        annee = np.arange(len(idx)) / 12
        m2_trend = 800 + annee * 8
        m2_rw = np.cumsum(rng.normal(0, 3, len(idx)))
        df["M2"] = np.maximum(m2_trend + m2_rw, 100)

    # --- INF ---
    # Priorité: INSTAT CPI réel (mensuel) > WB CPI interpolé > synthétique
    inf_ok = False
    if "INF_INSTAT" in reelles.columns:
        mask = reelles["INF_INSTAT"].notna()
        if mask.sum() > 0:
            df.loc[mask.index[mask], "INF"] = reelles["INF_INSTAT"][mask]
            inf_ok = True
            # Remplir début si nécessaire
            first_real = reelles["INF_INSTAT"].first_valid_index()
            if first_real is not None and first_real > idx[0]:
                # Utiliser WB CPI pour la période avant INSTAT
                if "CPI_WB" in reelles.columns:
                    # Convertir CPI_WB pour qu'il rejoigne INF_INSTAT
                    wb_before = reelles["CPI_WB"].loc[:first_real]
                    instat_start = reelles["INF_INSTAT"].loc[first_real]
                    # Normaliser WB au niveau INSTAT
                    ratio = instat_start / wb_before.iloc[-1] if wb_before.iloc[-1] != 0 else 1
                    wb_scaled = wb_before * ratio
                    df.loc[wb_scaled.index, "INF"] = wb_scaled

    if not inf_ok:
        if "CPI_WB" in reelles.columns:
            df["INF"] = reelles["CPI_WB"]
            print("[INFO] INF basée sur CPI Banque Mondiale (interpolé).")
        else:
            print("[WARN] INF non disponible, données synthétiques utilisées.")
            rng = np.random.default_rng(62)
            annee = np.arange(len(idx)) / 12
            df["INF"] = 90 + annee * 0.3 + np.cumsum(rng.normal(0, 1.5, len(idx)))
            df["INF"] = np.abs(df["INF"]) + 80

    # Arrondir
    for col in ["OIL", "EXR", "M2", "INF"]:
        if col in df.columns:
            df[col] = df[col].round(2)
            # Forward fill les trous éventuels
            df[col] = df[col].ffill()

    # Ajouter les dummies structurelles
    if ajouter_dummies:
        dummies = {
            "D2008": ("2008-09-01", "2009-06-01"),
            "D2020": ("2020-03-01", "2020-08-01"),
            "D2022": ("2022-02-01", "2022-12-01"),
        }
        for name, (start, end) in dummies.items():
            df[name] = ((df.index >= start) & (df.index <= end)).astype(float)

    df.columns.name = "Variable"
    df.index.name = "Date"
    return df


if __name__ == "__main__":
    print("=== Collecte de données réelles ===")
    df = generer_dataset_final()
    print(f"\nShape: {df.shape}")
    print(f"Index: {df.index[0].date()} -> {df.index[-1].date()}")
    print(f"\nPremières lignes:\n{df.head()}")
    print(f"\nStatistiques:\n{df[['OIL','EXR','M2','INF']].describe()}")
    
    # Sauvegarder
    from src.config import PROCESSED_DATA_FILE
    df.to_csv(PROCESSED_DATA_FILE)
    print(f"\nSauvegardé dans: {PROCESSED_DATA_FILE}")
