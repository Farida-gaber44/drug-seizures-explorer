"""Clean the IDS data using the decisions approved in reports/01_quality_check_summary.md.

Rows are never deleted: problems are flagged so every analysis can choose what to exclude
and the effect of each choice can be tested.

Input:  data/interim/ids_raw.parquet, data/reference/drug_class_lookup.csv
Output: data/processed/ids_clean.parquet, reports/02_cleaning_log.md
"""
import html
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INCOMPLETE_YEARS = {2025, 2026}          # late reporting: 64 and 32 countries vs ~85-100 before
OUTLIER_KG = 1_000_000                   # a single seizure of 1,000 tonnes or more is treated as an error
TO_KG = {"kg": 1.0, "g": 0.001}
SUBREGION_NAMES = {                      # same subregion spelled differently across the three files
    "Western and Central Europe": "West and Central Europe",
    "East Europe": "Eastern Europe",
    "Southeast Europe": "South-Eastern Europe",
    "South West Asia": "South-West Asia",
    "Central Asia and Transcaucasian countries": "Central Asia and Transcaucasia",
}
COUNTRY_NAMES = {                        # one name per ISO3 code
    "Macao S.A.R., China": "China, Macao SAR",
    "Netherlands": "Netherlands (Kingdom of the)",
}
# UNODC asks countries to report only "significant" seizures (IDS guidance note):
# cannabis and opium >= 1 kg; heroin, morphine, cocaine and psychotropic substances >= 100 g;
# new psychoactive substances: any quantity. Many countries report every seizure instead.
PLANT_MATERIAL_1KG = {"Opium", "Poppy plants", "Poppy straw", "Poppy seeds", "Extract from Opium poppy", "Pavots"}
DEFAULT_THRESHOLD_KG = 0.1
DUPLICATE_KEY =["seizure_date", "country", "admin_region", "city", "drug", "unit", "quantity",
                 "seizure_location", "transport_mode"]
DROPPED = ["seizure_location", "transport_mode", "source", "reporting_channel", "source_sheet"]


def city_key(name):
    """Lower-case, accent-free, punctuation-free city name so spelling variants group together."""
    if pd.isna(name):
        return name
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def significant(df):
    """True when the seizure meets UNODC's significant-seizure threshold.
    Rows not reported in g/kg cannot be checked and are marked False (conservative)."""
    nps = (df["unodc_class"] == "New psychoactive substances") | (df["project_group"] == "New psychoactive substances")
    one_kg = df["unodc_class"].str.startswith("Cannabis") | df["drug"].isin(PLANT_MATERIAL_1KG)
    threshold = pd.Series(DEFAULT_THRESHOLD_KG, index=df.index).where(~one_kg, 1.0)
    return nps | (df["weight_kg"] >= threshold)


def main() -> None:
    raw = pd.read_parquet(ROOT / "data" / "interim" / "ids_raw.parquet")
    lookup = pd.read_csv(ROOT / "data" / "reference" / "drug_class_lookup.csv")
    log = []

    df = raw.copy()
    df.insert(0, "case_id", range(1, len(df) + 1))

    before = df["subregion"].nunique()
    df["subregion"] = df["subregion"].replace(SUBREGION_NAMES)
    log.append(f"Subregion names merged: {before} -> {df['subregion'].nunique()}")

    for col in ["country", "city", "admin_region"]:          # e.g. "Côte d&#039;Ivoire"
        df[col] = df[col].map(lambda v: html.unescape(v) if isinstance(v, str) else v)
    before_c = df["country"].nunique()
    df["country"] = df["country"].replace(COUNTRY_NAMES)
    log.append(f"Country names: {before_c} -> {df['country'].nunique()} (one name per ISO3)")
    df["city_key"] = df["city"].map(city_key)
    log.append(f"City names: {df['city'].nunique():,} spellings -> {df.groupby('iso3')['city_key'].nunique().sum():,} city keys")

    df["month"] = df["seizure_date"].dt.month
    df["quarter"] = df["seizure_date"].dt.quarter
    df["is_incomplete_year"] = df["year"].isin(INCOMPLETE_YEARS)

    df = df.merge(lookup[["drug", "unodc_class", "project_group"]], on="drug", how="left")
    if df["project_group"].isna().any():
        raise ValueError(f"Drugs missing from lookup: {df.loc[df.project_group.isna(), 'drug'].unique()}")

    kg = df["unit"].map(TO_KG) * df["quantity"]
    df["is_invalid_quantity"] = df["quantity"] <= 0
    df["is_weight_outlier"] = kg >= OUTLIER_KG
    df["is_weighable"] = kg.notna() & ~df["is_invalid_quantity"] & ~df["is_weight_outlier"]
    df["weight_kg"] = kg.where(df["is_weighable"])

    df["is_duplicate"] = df.duplicated(subset=DUPLICATE_KEY + ["year"], keep="first")
    df["is_significant"] = significant(df)

    for col in ["source", "reporting_channel"]:
        log.append(f"Dropped `{col}`: values {df[col].value_counts().to_dict()}")
    df = df.drop(columns=DROPPED)

    order = ["case_id", "seizure_date", "year", "quarter", "month", "region", "subregion", "country",
             "iso3", "admin_region", "city", "city_key", "drug", "unodc_class", "project_group", "unit",
             "quantity", "weight_kg", "is_weighable", "is_invalid_quantity", "is_weight_outlier",
             "is_duplicate", "is_significant", "is_incomplete_year", "source_file"]
    df = df[order]
    out = ROOT / "data" / "processed" / "ids_clean.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    outliers = df[df["is_weight_outlier"]][["year", "country", "city", "drug", "quantity", "unit"]]
    groups = df.groupby("project_group").agg(rows=("case_id", "size"), weight_kg=("weight_kg", "sum"))
    groups["share_rows"] = (groups["rows"] / len(df)).map("{:.1%}".format)
    groups["weight_kg"] = groups["weight_kg"].map("{:,.0f}".format)

    report = f"""# Cleaning Log

**Run:** {date.today()} · script `scripts/04_clean.py` · decisions from `reports/01_quality_check_summary.md`
**Output:** `data/processed/ids_clean.parquet`, {len(df):,} rows (same as raw: no rows deleted, problems are flagged)

## What was done
| Step | Result |
|---|---|
| Subregion spellings merged | {log[0]} |
| Month and quarter added | from the real seizure date |
| Drug class added | `unodc_class` and `project_group` from `data/reference/drug_class_lookup.csv` (343 names, 185 classified by hand) |
| Weight in kg | `weight_kg` for g/kg rows: {df['is_weighable'].sum():,} rows ({df['is_weighable'].mean():.1%}) |
| Zero or negative quantity flagged | `is_invalid_quantity`: {df['is_invalid_quantity'].sum():,} rows (excluded from weight) |
| Weight outliers flagged (one seizure ≥ {OUTLIER_KG:,} kg) | `is_weight_outlier`: {df['is_weight_outlier'].sum():,} rows (excluded from weight) |
| Exact duplicates within a year flagged | `is_duplicate`: {df['is_duplicate'].sum():,} rows ({df['is_duplicate'].mean():.1%}), kept by default |
| UNODC "significant seizure" flag | `is_significant`: {df['is_significant'].sum():,} rows ({df['is_significant'].mean():.1%}); cannabis/opium ≥ 1 kg, other drugs ≥ 100 g, NPS any amount; non-g/kg rows = False |
| Incomplete years flagged | `is_incomplete_year`: 2025 and 2026, {df['is_incomplete_year'].sum():,} rows |
| Columns dropped | {', '.join(DROPPED)} |

{chr(10).join('- ' + line for line in log[1:])}

## Weight outliers
{outliers.to_markdown(index=False)}

## Rows by project group
{groups.to_markdown()}

## How to use the flags
- **Records (case counts):** use all rows; for a robustness check also run with `is_duplicate == False`.
- **Same rule for every country and year:** filter `is_significant == True` (countries differ in whether they report small seizures, and reporting changed around 2014).
- **City maps:** group by `iso3` + `city_key` (original `city` kept for labels).
- **Sharing:** publish aggregated tables only; UNODC asks that individual seizure records are not redistributed.
- **Weight:** use `weight_kg` (already excludes invalid and outlier rows).
- **Trends:** show 2025 and 2026 separately or marked as incomplete.
"""
    (ROOT / "reports" / "02_cleaning_log.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
