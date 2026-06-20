# Effet des chocs pétroliers sur l'inflation à Madagascar — SVAR (2000–2025)

[![Status](https://img.shields.io/badge/status-termin%C3%A9-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

Analyse de la transmission des chocs des prix internationaux du pétrole à l'inflation malgache, à l'aide d'un modèle **SVAR** identifié par décomposition de Cholesky. Données mensuelles réelles (Banque Mondiale, INSTAT) avec fallback synthétique.

📄 **Papier de recherche** : [`papier.pdf`](./papier.pdf) (19 pages, IMRED + état de l'art)
📓 **Notebook** : [`SVAR_Analysis.ipynb`](./SVAR_Analysis.ipynb)

---

## Résultats clés

| Résultat | Valeur |
|----------|--------|
| Réponse de l'inflation à un choc pétrolier | **−1,26 pts** d'IPC à $t+3$ (contre-intuitif : négatif) |
| Part de l'inflation expliquée par le pétrole (FEVD, 12 mois) | **< 1 %** |
| Part de l'inflation expliquée par ses propres chocs | **~90 %** → facteurs domestiques dominants |
| Stabilité du VAR | **Instable** (module max 3,1) → à interpréter avec prudence |
| Meilleur retard (AIC/BIC) | $p=1$ ; retenu $p=4$ pour capturer la dynamique de transmission |

> **Conclusion** : Le pétrole n'explique quasiment pas l'inflation à Madagascar. Les vrais moteurs sont domestiques (chocs agricoles, anticipations, prix administrés).

---

## Structure du projet

```
.
├── main.py                 # Pipeline CLI (6 étapes)
├── SVAR_Analysis.ipynb     # Notebook complet avec tous les résultats
├── papier.tex / .pdf       # Document de recherche formaté
├── src/
│   ├── config.py           # Paramètres (période, retards, dummies)
│   ├── collecte.py         # Collecte INSTAT + pétrole (locaux)
│   ├── collecte_reelle.py  # Collecte via API Banque Mondiale
│   ├── nettoyage.py        # Nettoyage, interpolation, assemblage
│   ├── analyse.py          # Statistiques, ADF/PP, Johansen, retards
│   ├── train.py            # VAR(p) + SVAR (Cholesky type B)
│   ├── diagnostics.py      # JB, Ljung-Box, CUSUM, White
│   └── utilisation.py      # IRF + FEVD + graphiques
├── data/
│   ├── raw/                # Données brutes (INSTAT Excel)
│   ├── processed/          # data.csv (301 obs × 7 variables)
│   └── external/           # Fichiers externes (pétrole Pink Sheet)
└── output/                 # 7 graphiques PNG
```

---

## Pipeline

```bash
# Tout exécuter
python main.py

# Étapes sélectives
python main.py --etapes=collecte,nettoyage,analyse
python main.py --etapes=train,utilisation
```

Les 6 étapes :

1. **collecte** — extraction des fichiers Excel (INSTAT CPI, Brent Pink Sheet)
2. **nettoyage** — interpolation annuel→mensuel, raccordement CPI, dummies, fallback synthétique
3. **analyse** — stats descriptives, ADF/PP, Johansen, sélection retards
4. **train** — VAR(p) + SVAR (Cholesky, type B, $p=4$, dummies exogènes)
5. **diagnostics** — JB, Ljung-Box, CUSUM, White
6. **utilisation** — IRF (30 périodes), FEVD, graphiques

---

## Données : sources réelles + fallback synthétique

| Variable | Source principale | Fréquence | API |
|----------|-------------------|-----------|-----|
| **OIL** | World Bank Pink Sheet (Brent) | Mensuelle | Fichier Excel local |
| **EXR** | Banque Mondiale PA.NUS.FCRF | Annuelle → interpolée | `api.worldbank.org` |
| **M2** | Banque Mondiale FM.LBL.BMNY.CN | Annuelle → interpolée | `api.worldbank.org` |
| **INF** | INSTAT (2016+) + WB FP.CPI.TOTL (2000–2015) | Mensuelle + annuelle | Mixte |

**Dummies structurelles** : D2008 (crise), D2020 (COVID), D2022 (Ukraine)

---

## Installation

```bash
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate # Linux/Mac

pip install -r requirements.txt
```

**Dépendances** : `pandas`, `numpy`, `matplotlib`, `statsmodels`, `scipy`, `requests`, `openpyxl`, `jupyter`

---

## Configuration

Tous les paramètres dans [`src/config.py`](./src/config.py) :

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `DATE_START` | `2000-01-01` | Début période |
| `DATE_END` | `2025-01-01` | Fin période |
| `SVAR_LAGS` | `4` | Nombre de retards |
| `SVAR_TYPE` | `"B"` | `"A"` ou `"B"` |
| `SVAR_ORDERING` | `["OIL","EXR","M2","INF"]` | Ordre de Cholesky |

---

## Références

- Sims, C. A. (1980). *Macroeconomics and reality*. Econometrica.
- Bernanke, B. S. (1986). *Alternative explanations of the money-income correlation*. Carnegie-Rochester Conference.
- Kilian, L., & Lütkepohl, H. (2017). *Structural Vector Autoregressive Analysis*. Cambridge University Press.
- Hamilton, J. D. (1983). *Oil and the macroeconomy since World War II*. Journal of Political Economy.
- Ramiandrisoa, T., & Randriambola, S. (2019). *Déterminants de l'inflation à Madagascar*. Bulletin BFM.
