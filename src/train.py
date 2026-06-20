import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR, SVAR
from src.config import OUTPUT_DIR, SVAR_LAGS, SVAR_TYPE, SVAR_ORDERING, SVAR_VARIABLES


def _exog_from_df(df, trim_to=None):
    dummy_cols = [c for c in df.columns if c.startswith("D")]
    if not dummy_cols:
        return None
    exog = df[dummy_cols].values
    if trim_to is not None and len(exog) > trim_to:
        exog = exog[-trim_to:]
    return exog


def estimer_var(df_d1, p=None, exog=None):
    if p is None:
        p = SVAR_LAGS
    print("\n" + "=" * 60)
    print(f"ESTIMATION VAR (p={p})")
    print("=" * 60)
    model = VAR(df_d1, exog=exog)
    results = model.fit(p)
    print(results.summary())
    return results


def verifier_stabilite(var_results, df_columns):
    print("\n" + "=" * 60)
    print("STABILITÉ DU VAR")
    print("=" * 60)
    roots = var_results.roots
    for i, r in enumerate(roots):
        print(f"  Racine {i+1}: {r:.4f}")
    max_mod = max(abs(r) for r in roots)
    print(f"  Module maximal: {max_mod:.4f}")
    status = "STABLE" if max_mod < 1 else "INSTABLE"
    print(f"  => {status}")

    fig, ax = plt.subplots(figsize=(7, 7))
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), "k--", alpha=0.3)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    for r in roots:
        ax.plot(r.real, r.imag, "ro", markersize=6)
    ax.set_aspect("equal")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_title(f"Cercle unité et racines du VAR (p={SVAR_LAGS})")
    path = OUTPUT_DIR / "stabilite_var.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Graphique: {path}")
    plt.close()
    return status


def _matrice_restrictions(variables, svar_type):
    n = len(variables)
    if svar_type.upper() == "A":
        # Ae = u : A triangulaire inférieure avec 1 sur la diagonale
        A = np.array([
            [1 if i == j else ("E" if i > j else 0) for j in range(n)]
            for i in range(n)
        ])
        return None, A
    else:
        # e = Bu : B triangulaire inférieure
        B = np.array([
            ["E" if i >= j else 0 for j in range(n)]
            for i in range(n)
        ])
        return B, None


def identification_svar(df_d1, variables, p=None, ordering=None, svar_type=None, exog=None):
    if p is None:
        p = SVAR_LAGS
    if ordering is None:
        ordering = SVAR_ORDERING
    if svar_type is None:
        svar_type = SVAR_TYPE

    print("\n" + "=" * 60)
    print(f"IDENTIFICATION SVAR (type={svar_type.upper()}, retards={p})")
    print(f"  Ordre des variables: {ordering}")
    print("=" * 60)

    df_ordered = df_d1[ordering].copy()
    n = len(ordering)
    B, A = _matrice_restrictions(ordering, svar_type)

    if svar_type.upper() == "A":
        model = SVAR(df_ordered, svar_type="A", A=A)
        print("  Matrice A (triangulaire inférieure, diag=1):")
        for row in A:
            print(f"    {row}")
    else:
        model = SVAR(df_ordered, svar_type="B", B=B)
        print("  Matrice B (triangulaire inférieure):")
        for row in B:
            print(f"    {row}")

    results = model.fit(p)

    label = results.A if svar_type.upper() == "A" else results.B
    mat = pd.DataFrame(label, index=ordering, columns=ordering).round(4)
    print(f"\n  Matrice {svar_type.upper()} estimée (impact contemporain):")
    print(mat)

    shocks = pd.Series(
        np.diag(results.sigma_u_mle) ** 0.5, index=ordering
    ).round(4)
    print("\n  Ecarts-types des chocs structurels:")
    print(shocks)
    return results


def entrainer_complet(df, df_d1, p=None, variables=None):
    if p is None:
        p = SVAR_LAGS
    if variables is None:
        variables = SVAR_VARIABLES
    exog = _exog_from_df(df, trim_to=len(df_d1))
    if exog is not None and exog.shape[1] > 0:
        dummy_names = [c for c in df.columns if c.startswith("D")]
        print(f"[Train] Muettes exogènes incluses: {dummy_names}")

    var_results = estimer_var(df_d1, p, exog=exog)
    verifier_stabilite(var_results, variables)
    svar_results = identification_svar(df_d1, variables, p)
    return var_results, svar_results


if __name__ == "__main__":
    df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
    var_cols = [c for c in df.columns if not c.startswith("D")]
    df_vars = df[var_cols]
    df_d1 = df_vars.diff().dropna()
    entrainer_complet(df, df_d1)
