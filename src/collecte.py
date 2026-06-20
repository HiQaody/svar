import pandas as pd
from src.config import RAW_CPI_FILE, RAW_OIL_FILE, DATE_START, DATE_END


def collecter_cpi():
    df = pd.read_excel(RAW_CPI_FILE, header=None)
    valeurs = df.iloc[13, 2:].astype(float)
    dates = pd.to_datetime(df.iloc[12, 2:], errors="coerce")
    cpi = pd.Series(valeurs.values, index=dates, name="IPC_Niveau")
    cpi = cpi[cpi.index.notna()].sort_index()
    return cpi


def collecter_oil():
    df = pd.read_excel(RAW_OIL_FILE, header=None)
    valeurs = df.iloc[2:, 3].astype(float)
    dates = pd.to_datetime(df.iloc[2:, 1], errors="coerce")
    oil = pd.Series(valeurs.values, index=dates, name="OIL_Brent")
    oil = oil[oil.index.notna()].sort_index()
    return oil


def collecter_tout():
    cpi = collecter_cpi()
    oil = collecter_oil()
    print(f"[Collecte] CPI: {len(cpi)} obs ({cpi.index[0].date()} - {cpi.index[-1].date()})")
    print(f"[Collecte] Oil: {len(oil)} obs ({oil.index[0].date()} - {oil.index[-1].date()})")
    return {"cpi": cpi, "oil": oil}


if __name__ == "__main__":
    collecter_tout()
