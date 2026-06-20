import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.tsa.api import VAR
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from scipy.stats import chi2, norm
from src.config import OUTPUT_DIR, SVAR_LAGS


def test_adf(series, name):
    result = adfuller(series.dropna(), autolag="AIC")
    print(f"  ADF ({name}): stats={result[0]:.4f}, p-value={result[1]:.4f}"
          f" => {'Stationnaire' if result[1] <= 0.05 else 'Non-stationnaire'}")
    return result[1]


def test_pp(series, name):
    y = series.dropna().values
    n = len(y)
    dy = np.diff(y)
    y_lag = y[:-1]
    X = add_constant(np.column_stack([y_lag, np.arange(n - 1)]))
    res = OLS(dy, X).fit()
    rho = res.params[1]
    se = res.bse[1]
    stat = (rho - 1) / se
    pval = 2 * norm.cdf(-abs(stat))
    print(f"  PP  ({name}): stats={stat:.4f}, p-value={pval:.4f}"
          f" => {'Stationnaire' if pval <= 0.05 else 'Non-stationnaire'}")
    return pval


def analyser_stationnarite(df):
    print("\n" + "=" * 60)
    print("TESTS DE STATIONNARITÉ (ADF & PP)")
    print("=" * 60)
    for col in df.columns:
        p_adf = test_adf(df[col], col)
        p_pp = test_pp(df[col], col)

    df_d1 = df.diff().dropna()
    print("\nSéries différenciées (I(1)):")
    for col in df_d1.columns:
        test_adf(df_d1[col], f"{col} (diff)")
        test_pp(df_d1[col], f"{col} (diff)")
    return df_d1


def analyser_cointegration(df, det_order=0, k_ar_diff=2):
    print("\n" + "=" * 60)
    print("TEST DE COINTÉGRATION (JOHANSEN)")
    print("=" * 60)
    result = coint_johansen(df.values, det_order, k_ar_diff)
    print(f"  Trace statistics:  {result.lr1.round(3)}")
    print(f"  Critical values:   {result.cvt[:, 1].round(3)}")
    r = sum(result.lr1 > result.cvt[:, 1])
    print(f"  Rang de cointégration: {r}")
    if r > 0:
        print("  [Note] Cointégration détectée -> VECM alternatif possible")
    return r


def analyser_retards_optimaux(df_d1, maxlags=12):
    print("\n" + "=" * 60)
    print("SÉLECTION DU NOMBRE DE RETARDS")
    print("=" * 60)
    model = VAR(df_d1)
    selection = model.select_order(maxlags)
    print(selection.summary())
    p_aic = int(selection.aic)
    p_bic = int(selection.bic)

    # Comparer avec la valeur configurée
    print(f"\n  AIC:  p = {p_aic}")
    print(f"  BIC:  p = {p_bic}")
    print(f"  Config: p = {SVAR_LAGS}")
    if SVAR_LAGS != p_aic:
        print(f"  -> Utilisation de p={SVAR_LAGS} (configuré) au lieu de p={p_aic} (AIC)")

    return p_aic


def analyse_factorielle(df):
    print("\n" + "=" * 60)
    print("STATISTIQUES DESCRIPTIVES")
    print("=" * 60)
    print(df.describe().round(2))

    fig, axes = plt.subplots(len(df.columns), 1, figsize=(12, 8), sharex=True)
    for ax, col in zip(axes, df.columns):
        ax.plot(df.index, df[col], linewidth=1.5)
        ax.set_title(col)
        ax.set_ylabel("")
    plt.tight_layout()
    path = OUTPUT_DIR / "descriptives.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()


def analyser_complet(df):
    analyse_factorielle(df)
    df_d1 = analyser_stationnarite(df)
    analyser_cointegration(df_d1)
    p_opt = analyser_retards_optimaux(df_d1)
    print(f"\n  Retards utilisé dans train: p = {SVAR_LAGS}")
    return df_d1, SVAR_LAGS


if __name__ == "__main__":
    df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
    var_cols = [c for c in df.columns if not c.startswith("D")]
    df = df[var_cols]
    analyser_complet(df)
