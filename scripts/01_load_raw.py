"""Load the three UNODC IDS Excel exports into one Parquet file.

Source: UNODC Drugs Monitoring Platform, https://dmp.unodc.org/downloadIDS
Each Excel file has one sheet per year plus a 'Drug list and Measurement Units' sheet.
Column order and names differ between files (e.g. the 'Subrgion' typo), so every sheet
is renamed to one standard schema before stacking. No rows are dropped here.
"""
from pathlib import Path
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

FILES = [
    "IDS-data-2011_17-May24.xlsx",
    "IDS-data-2018-2022.xlsx",
    "IDS-data-2023-2026-V1.xlsx",
]
DRUG_LIST_SHEET = "Drug list and Measurement Units"

COLUMNS = {
    "Seizure Date": "seizure_date",
    "Country/Territory of Seizure": "country",
    "ISO3": "iso3",
    "Region": "region",
    "Subregion": "subregion",
    "Subrgion": "subregion",
    "City": "city",
    "Administrative Region": "admin_region",
    "Drug/Substance": "drug",
    "Measurement Unit": "unit",
    "Quantity Seized": "quantity",
    "Physical Seizure Location": "seizure_location",
    "Trafficking Mode of Transportation": "transport_mode",
    "Source": "source",
    "Reporting Channel": "reporting_channel",
}
TEXT_COLUMNS = [c for c in dict.fromkeys(COLUMNS.values()) if c not in ("seizure_date", "quantity")]


def load_file(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine="openpyxl")
    frames = []
    for name, df in sheets.items():
        if name == DRUG_LIST_SHEET:
            continue
        unknown = set(df.columns) - set(COLUMNS)
        if unknown:
            raise ValueError(f"{path.name}/{name}: unexpected columns {unknown}")
        df = df.rename(columns=COLUMNS)
        df["source_file"] = path.name
        df["source_sheet"] = name
        frames.append(df)
        print(f"  {path.name} / {name}: {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)


def save_drug_list(path: Path) -> None:
    drugs = pd.read_excel(path, sheet_name=DRUG_LIST_SHEET, dtype=str, engine="openpyxl")
    drugs = drugs.iloc[:, :3]
    drugs.columns = ["drug_class", "drug", "drug_subgroup"]
    for c in drugs.columns:
        drugs[c] = drugs[c].str.replace("\xa0", " ").str.strip()
    drugs = drugs.dropna(subset=["drug"]).drop_duplicates()
    drugs.to_csv(INTERIM / "unodc_drug_list.csv", index=False, encoding="utf-8")
    print(f"  drug list: {len(drugs)} drugs, {drugs['drug_class'].nunique()} classes")


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    start = time.time()

    df = pd.concat([load_file(RAW / f) for f in FILES], ignore_index=True)

    for c in TEXT_COLUMNS:
        df[c] = df[c].str.replace("\xa0", " ").str.strip()
    df["seizure_date"] = pd.to_datetime(df["seizure_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["year"] = df["source_sheet"].astype(int)

    df.to_parquet(INTERIM / "ids_raw.parquet", index=False)
    save_drug_list(RAW / FILES[-1])

    print(f"Saved {len(df):,} rows to {INTERIM / 'ids_raw.parquet'} in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
