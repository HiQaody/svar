Pour la thématique :

# **« Effet des prix du pétrole sur l'inflation à Madagascar : une approche SVAR »**

voici les **sources de données recommandées**, les variables associées, la fréquence des données et les liens d'accès.

| Variable | Description                       | Fréquence | Source principale             | Période disponible           |
| -------- | --------------------------------- | --------- | ----------------------------- | ---------------------------- |
| **INF**  | Inflation (IPC/NIPC)              | Mensuelle | INSTAT Madagascar             | 2001–2026                    |
| **OIL**  | Prix du pétrole Brent (USD/baril) | Mensuelle | Banque Mondiale (Pink Sheet)  | 1960–2026                    |
| **EXR**  | Taux de change MGA/USD            | Mensuelle | Banque Centrale de Madagascar | 1994–2026                    |
| **M2**   | Masse monétaire M2                | Mensuelle | Banque Centrale de Madagascar | Variable selon disponibilité |
| **TDR**  | Taux directeur                    | Mensuelle | Banque Centrale de Madagascar | Variable selon disponibilité |

---

# 1. Inflation (IPC)

### Source

**INSTAT Madagascar**

### Données disponibles

* Indice des Prix à la Consommation (IPC)
* Taux d'inflation
* Série mensuelle

### Lien

[INSTAT Madagascar – Base NIPC (IPC)](https://www.instat.mg/statistiques/bases-de-donnees/nipc)

### Variable dans le modèle

```
INF
```

---

# 2. Prix international du pétrole Brent

### Source

Banque Mondiale (Pink Sheet Commodity Prices)

### Données disponibles

* Brent crude oil price
* Prix moyen mondial du pétrole
* Série mensuelle en USD/baril

### Lien

[World Bank Pink Sheet Oil Prices](https://www.fetchseries.com/oil/oil-prices-world-bank-pink-sheets/)

### Variable

```
OIL
```

---

# 3. Taux de change Ariary/USD

### Source principale

Banque Centrale de Madagascar (BFM)

### Sources alternatives

* Direction Générale des Douanes Malagasy
* IMF International Financial Statistics

### Lien

[Cours de change Madagascar](https://www.douanes.gov.mg/cours-de-change/?utm_source=chatgpt.com)

### Variable

```
EXR
```

---

# 4. Masse monétaire M2

### Source

Banque Centrale de Madagascar

### Publication

* Bulletins statistiques
* Rapports annuels

### Variable

```
M2
```

---

# 5. Taux directeur

### Source

Banque Centrale de Madagascar

### Variable

```
TDR
```

---

# Sources internationales alternatives

## Banque Mondiale (WDI)

Variables :

* Inflation
* Taux de change
* Masse monétaire
* PIB

Site :

[World Development Indicators (WDI)](https://databank.worldbank.org/source/world-development-indicators?utm_source=chatgpt.com)

---

## FMI (IFS)

Variables :

* Inflation
* Taux de change
* M2
* Taux d'intérêt

Site :

[IMF Data – International Financial Statistics](https://data.imf.org/?utm_source=chatgpt.com)

---

## FRED (Federal Reserve Economic Data)

Variables :

* Brent Crude Oil Price
* Inflation mondiale
* Taux d'intérêt américains

Site :

[FRED Economic Data](https://fred.stlouisfed.org/?utm_source=chatgpt.com)

---

# Jeu de données recommandé pour un mémoire SVAR (simple et robuste)

| Variable               | Symbole | Source          |
| ---------------------- | ------- | --------------- |
| Prix du pétrole Brent  | OIL     | Banque Mondiale |
| Taux de change MGA/USD | EXR     | BFM             |
| Masse monétaire M2     | M2      | BFM             |
| Inflation (IPC)        | INF     | INSTAT          |

Vecteur SVAR :

[
Y_t=(OIL_t,\ EXR_t,\ M2_t,\ INF_t)
]

avec des **données mensuelles de janvier 2001 à décembre 2025**, ce qui fournit environ **300 observations**, largement suffisantes pour estimer un modèle SVAR et effectuer les analyses IRF et FEVD. ([instat.mg][1])

[1]: https://www.instat.mg/statistiques/bases-de-donnees/nipc?utm_source=chatgpt.com "INSTAT Madagascar - Institut National de la Statistique"
