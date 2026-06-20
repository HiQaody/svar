import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import chi2, norm, jarque_bera
from statsmodels.tsa.stattools import acf
from src.config import OUTPUT_DIR


def test_normalite(residuals, variables):
    print("\n" + "=" * 60)
    print("TEST DE NORMALITÉ (JARQUE-BERA)")
    print("=" * 60)
    for i, name in enumerate(variables):
        stat, pval = jarque_bera(residuals[:, i])
        print(f"  {name}: JB={stat:.4f}, p-value={pval:.4f}"
              f" => {'Normal' if pval > 0.05 else 'Non-normal'}")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for i, (name, ax) in enumerate(zip(variables, axes.flatten())):
        ax.hist(residuals[:, i], bins=25, edgecolor="black", alpha=0.7, density=True)
        x = np.linspace(residuals[:, i].min(), residuals[:, i].max(), 100)
        ax.plot(x, norm.pdf(x, residuals[:, i].mean(), residuals[:, i].std()),
                "r-", linewidth=2)
        ax.set_title(f"Résidus : {name}")
    plt.tight_layout()
    path = OUTPUT_DIR / "diagnostic_normalite.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()


def test_autocorrelation(residuals, variables, nlags=10):
    print("\n" + "=" * 60)
    print("TEST D'AUTOCORRÉLATION (PORTMANTEAU / Ljung-Box)")
    print("=" * 60)
    for i, name in enumerate(variables):
        acf_vals = acf(residuals[:, i], nlags=nlags, fft=True)
        q_stat = len(residuals) * np.sum(acf_vals[1:] ** 2)
        pval = 1 - chi2.cdf(q_stat, nlags)
        print(f"  {name}: Q-stat={q_stat:.4f}, p-value={pval:.4f}"
              f" => {'Aucune autocorrélation' if pval > 0.05 else 'Autocorrélation présente'}")

    print("\n  Matrice de corrélation contemporaine des résidus :")
    corr = np.corrcoef(residuals.T)
    print(pd.DataFrame(corr, index=variables, columns=variables).round(4))


def test_cusum(residuals, variables, df_d1, p):
    print("\n" + "=" * 60)
    print("TEST DE STABILITÉ STRUCTURELLE (CUSUM)")
    print("=" * 60)
    nobs = len(df_d1)
    resid_std = (residuals - residuals.mean(axis=0)) / residuals.std(axis=0)
    cusum = resid_std.cumsum(axis=0) / (nobs ** 0.5)
    crit = 0.948

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    n_resid = len(residuals)
    start = nobs - n_resid
    date_idx = df_d1.index[start:]
    for i, (name, ax) in enumerate(zip(variables, axes.flatten())):
        ax.plot(date_idx, cusum[:, i], linewidth=1.5)
        ax.axhline(crit, color="r", linestyle="--", alpha=0.5, label=f"+{crit}")
        ax.axhline(-crit, color="r", linestyle="--", alpha=0.5, label=f"-{crit}")
        ax.set_title(f"CUSUM : {name}")
        ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "diagnostic_cusum.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()


def test_heteroscedasticite(residuals, variables, exog_lags):
    print("\n" + "=" * 60)
    print("TEST D'HÉTÉROSCÉDASTICITÉ (WHITE)")
    print("=" * 60)
    n = len(residuals)
    exog = exog_lags[:n]
    for i, name in enumerate(variables):
        resid2 = residuals[:, i] ** 2
        exog_const = np.column_stack([np.ones(n), exog])
        try:
            beta = np.linalg.lstsq(exog_const, resid2, rcond=None)[0]
            fitted = exog_const @ beta
            r2 = 1.0 - np.sum((resid2 - fitted) ** 2) / max(np.sum((resid2 - resid2.mean()) ** 2), 1e-30)
            stat = n * r2
            k = exog_const.shape[1]
            pval = 1.0 - chi2.cdf(stat, k)
        except np.linalg.LinAlgError:
            print(f"  {name}: test non concluant (matrice singulière)")
            continue
        print(f"  {name}: stat={stat:.4f}, p-value={pval:.4f}"
              f" => {'Homoscédasticité' if pval > 0.05 else 'Hétéroscédasticité [WARN]'}")


def diagnostiquer_complet(var_results, svar_results, df_d1, p, variables):
    residuals = svar_results.resid
    print("\n" + "#" * 70)
    print("# DIAGNOSTICS DU MODÈLE")
    print("#" * 70)

    test_normalite(residuals, variables)
    test_autocorrelation(residuals, variables)
    test_cusum(residuals, variables, df_d1, p)

    n_resid = len(residuals)
    n_total = len(df_d1)
    start = n_total - n_resid
    lagged = [df_d1.shift(l).iloc[start:].values for l in range(1, p + 1)]
    exog_lags = np.column_stack(lagged)
    test_heteroscedasticite(residuals, variables, exog_lags)

    print("\n" + "#" * 70)
    print("# DIAGNOSTICS TERMINÉS")
    print("#" * 70)


if __name__ == "__main__":
    df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
    df_d1 = df.diff().dropna()
    from src.train import entrainer_complet
    var_res, svar_res = entrainer_complet(df, df_d1, p=2)
    diagnostiquer_complet(var_res, svar_res, df_d1, 2, list(df.columns))
