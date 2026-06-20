import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.vector_ar.var_model import FEVD
from src.config import OUTPUT_DIR, SVAR_LAGS


def irf_analysis(svar_results, variables, periods=30):
    print("\n" + "=" * 60)
    print("FONCTIONS DE RÉPONSE IMPULSIONNELLE (IRF)")
    print("=" * 60)
    irf = svar_results.irf(periods)

    print(f"  Réponse de INF à un choc OIL (12 premiers mois):")
    inf_idx = variables.index("INF")
    oil_idx = variables.index("OIL")
    print(f"  {irf.irfs[:12, oil_idx, inf_idx]}")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_list = axes.flatten()
    pairs = [
        ("OIL", "INF"), ("EXR", "INF"),
        ("M2", "INF"), ("OIL", "EXR"),
    ]
    for ax, (imp, resp) in zip(ax_list, pairs):
        irf.plot(impulse=imp, response=resp, subplot_params={"ax": ax})
        ax.set_title(f"{resp} -> choc {imp}")
    plt.tight_layout()
    path = OUTPUT_DIR / "irf.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()

    irf_cum = svar_results.irf(periods)
    irf_cum.plot_cum_effects(impulse="OIL", response="INF")
    plt.title(f"Réponse cumulée de INF à un choc OIL (p={SVAR_LAGS})")
    path = OUTPUT_DIR / "irf_cumulee.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique cumulé: {path}")
    plt.close()

    return irf


def fevd_analysis(var_results, variables, periods=30):
    print("\n" + "=" * 60)
    print("DÉCOMPOSITION DE LA VARIANCE (FEVD)")
    print("=" * 60)
    P = np.linalg.cholesky(var_results.sigma_u).T
    fevd = FEVD(var_results, P=P, periods=periods)

    inf_idx = variables.index("INF")
    fevd_df = pd.DataFrame(
        fevd.decomp[inf_idx, :, :],
        columns=variables,
        index=[f"t+{i+1}" for i in range(periods)],
    )
    print(f"  Variance de INF expliquée par chaque choc (p={SVAR_LAGS}):")
    print(fevd_df.round(4).head(12))

    fig, ax = plt.subplots(figsize=(14, 6))
    fevd_df[[c for c in fevd_df.columns if c != "INF"]].plot(ax=ax)
    ax.set_title(f"Contribution des chocs à la variance de INF (p={SVAR_LAGS})")
    ax.set_xlabel("Horizon")
    ax.set_ylabel("Part de variance")
    ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "fevd.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()

    return fevd_df


if __name__ == "__main__":
    from statsmodels.tsa.api import VAR
    df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
    var_cols = [c for c in df.columns if not c.startswith("D")]
    df = df[var_cols]
    df_d1 = df.diff().dropna()
    from src.train import entrainer_complet
    var_res, svar_res = entrainer_complet(df, df_d1)
    irf_analysis(svar_res, var_cols)
    fevd_analysis(var_res, var_cols)
