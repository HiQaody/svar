import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_EXTERNAL = PROJECT_ROOT / "data" / "external"
OUTPUT_DIR = PROJECT_ROOT / "output"

for d in [DATA_RAW, DATA_PROCESSED, DATA_EXTERNAL, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RAW_CPI_FILE = DATA_RAW / "INSTAT_NIPC-Mars-2026.xlsx"
RAW_OIL_FILE = DATA_EXTERNAL / "oil-prices-world-bank-pink-sheets.xlsx"
PROCESSED_DATA_FILE = DATA_PROCESSED / "data.csv"

DATE_START = "2000-01-01"
DATE_END = "2025-01-01"
FREQ = "MS"

# SVAR parameters
SVAR_VARIABLES = ["OIL", "EXR", "M2", "INF"]
SVAR_LAGS = 4
SVAR_TYPE = "B"           # "B" (e = Bu) ou "A" (Ae = u)
SVAR_ORDERING = ["OIL", "EXR", "M2", "INF"]  # ordre Cholesky

# Dummies for structural breaks
DUMMY_DATES = {
    "D2008": ("2008-09-01", "2009-06-01"),
    "D2020": ("2020-03-01", "2020-08-01"),
    "D2022": ("2022-02-01", "2022-12-01"),
}
