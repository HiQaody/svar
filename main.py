"""
Pipeline SVAR: Effet des prix du pétrole sur l'inflation à Madagascar

Usage:
    python main.py [--etapes collecte,nettoyage,analyse,train,diagnostics,utilisation]

Étapes:
    1. collecte     - Chargement des données brutes
    2. nettoyage    - Nettoyage, alignment, muettes structurelles
    3. analyse      - Stats, stationnarité (ADF, PP), cointégration, retards
    4. train        - VAR(p) + SVAR (Cholesky, type A/B configurable)
    5. diagnostics  - Normalité, autocorrélation, CUSUM, hétéroscédasticité
    6. utilisation  - IRF, FEVD, graphiques

Configuration dans src/config.py :
  SVAR_LAGS, SVAR_TYPE, SVAR_ORDERING, DUMMY_DATES
"""

import sys
import pandas as pd
from src.collecte import collecter_tout
from src.nettoyage import nettoyer_et_sauvegarder
from src.analyse import analyser_complet
from src.train import entrainer_complet
from src.diagnostics import diagnostiquer_complet
from src.utilisation import irf_analysis, fevd_analysis
from src.config import SVAR_VARIABLES


ETAPES_DISPONIBLES = [
    "collecte", "nettoyage", "analyse",
    "train", "diagnostics", "utilisation"
]


def _cols_var(df):
    return [c for c in df.columns if not c.startswith("D")]


def executer_etapes(etapes):
    donnees = None
    df = None
    df_vars = None
    df_d1 = None
    p = None
    var_results = None
    svar_results = None
    variables = SVAR_VARIABLES

    for etape in etapes:
        print(f"\n{'#' * 70}")
        print(f"# ÉTAPE: {etape.upper()}")
        print(f"{'#' * 70}")

        if etape == "collecte":
            donnees = collecter_tout()

        elif etape == "nettoyage":
            if donnees is None:
                from src.collecte import collecter_cpi, collecter_oil
                donnees = {"cpi": collecter_cpi(), "oil": collecter_oil()}
            df = nettoyer_et_sauvegarder(donnees)

        elif etape == "analyse":
            if df is None:
                df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
            df_vars = df[_cols_var(df)]
            df_d1, p = analyser_complet(df_vars)

        elif etape == "train":
            if df is None or df_d1 is None or p is None:
                df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
                df_vars = df[_cols_var(df)]
                df_d1, p = analyser_complet(df_vars)
            var_results, svar_results = entrainer_complet(df, df_d1, p, variables)

        elif etape == "diagnostics":
            if svar_results is None or df_d1 is None:
                df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
                df_vars = df[_cols_var(df)]
                df_d1 = df_vars.diff().dropna()
                from src.train import estimer_var, identification_svar
                var_results_ = estimer_var(df_d1)
                svar_results_ = identification_svar(df_d1, variables)
                var_results, svar_results = var_results_, svar_results_
            diagnostiquer_complet(var_results, svar_results, df_d1, p, variables)

        elif etape == "utilisation":
            if var_results is None or svar_results is None:
                df = pd.read_csv("data/processed/data.csv", index_col=0, parse_dates=True)
                df_vars = df[_cols_var(df)]
                df_d1 = df_vars.diff().dropna()
                from src.train import estimer_var, identification_svar
                var_results_ = estimer_var(df_d1)
                svar_results_ = identification_svar(df_d1, variables)
                var_results, svar_results = var_results_, svar_results_
            irf_analysis(svar_results, variables)
            fevd_analysis(var_results, variables)

    print(f"\n{'#' * 70}")
    print(f"# PIPELINE TERMINÉ")
    print(f"{'#' * 70}")


def main():
    etapes = ETAPES_DISPONIBLES
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("--etapes="):
            etapes = arg.split("=", 1)[1].split(",")
            etapes = [e.strip() for e in etapes if e.strip() in ETAPES_DISPONIBLES]

    print(f"Pipeline SVAR - Étapes: {', '.join(etapes)}")
    print(f"  Retards (p): {__import__('src.config', fromlist=['SVAR_LAGS']).SVAR_LAGS}")
    print(f"  Type SVAR:   {__import__('src.config', fromlist=['SVAR_TYPE']).SVAR_TYPE}")
    print(f"  Ordre:       {__import__('src.config', fromlist=['SVAR_ORDERING']).SVAR_ORDERING}")
    executer_etapes(etapes)


if __name__ == "__main__":
    main()
