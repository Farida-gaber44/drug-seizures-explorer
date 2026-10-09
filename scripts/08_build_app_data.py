"""Build the aggregated data used by the Streamlit app (app/app.py).

The app never loads individual seizure records: it uses one row per
year x country x drug with counts and weights. This keeps the app fast and follows
UNODC's request not to redistribute individual seizure records.

Also builds the COVID-19 view: monthly records 2019-2021 for a fixed panel of countries
(>= 100 records in every year 2018-2021, so reporting changes cannot create the dip),
as an index where 100 = the 2018-2019 average for the same month.

Input:  data/processed/ids_clean.parquet, data/processed/signals/mena_signals.csv
Output: app/data/ids_summary.parquet, app/data/mena_signals.csv,
        app/data/covid_monthly.csv, app/data/covid_panel_countries.csv
"""
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "data"
KEYS = ["year", "region", "subregion", "country", "iso3", "project_group", "unodc_class", "drug"]
COVID_YEARS, BASELINE_YEARS, PANEL_MIN = [2018, 2019, 2020, 2021], [2018, 2019], 100
DRUG_GROUPS = ["Plant-based", "Synthetic", "Pharmaceutical", "New psychoactive substances"]


def build_covid(df: pd.DataFrame) -> None:
    d = df[df["year"].isin(COVID_YEARS)]
    per_year = d.groupby(["country", "year"]).size().unstack(fill_value=0)
    panel = per_year[(per_year >= PANEL_MIN).all(axis=1)].index
    d = d[d["country"].isin(panel)]

    frames = [d.assign(group="All drugs")] + [d[d["project_group"] == g].assign(group=g) for g in DRUG_GROUPS]
    m = pd.concat(frames).groupby(["group", "year", "month"]).size().rename("records").reset_index()
    base = (m[m["year"].isin(BASELINE_YEARS)].groupby(["group", "month"])["records"].mean()
            .rename("baseline_2018_19").reset_index())
    m = m[m["year"] >= 2019].merge(base, on=["group", "month"])
    m["index"] = (m["records"] / m["baseline_2018_19"] * 100).round(1)
    m["date"] = pd.to_datetime(dict(year=m["year"], month=m["month"], day=1))
    m.to_csv(OUT / "covid_monthly.csv", index=False)
    pd.Series(sorted(panel), name="country").to_csv(OUT / "covid_panel_countries.csv", index=False)
    april = m[(m["group"] == "All drugs") & (m["year"] == 2020) & (m["month"] == 4)]["index"].iloc[0]
    print(f"COVID view: {len(panel)} panel countries, April 2020 index = {april:.0f}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(ROOT / "data" / "processed" / "ids_clean.parquet",
                         columns=KEYS + ["month", "case_id", "weight_kg", "is_weighable", "is_significant"])
    build_covid(df)
    df["significant_kg"] = df["weight_kg"].where(df["is_significant"])

    agg = df.groupby(KEYS, observed=True).agg(
        records=("case_id", "size"),
        significant_records=("is_significant", "sum"),
        weighable_records=("is_weighable", "sum"),
        weight_kg=("weight_kg", "sum"),
        significant_kg=("significant_kg", "sum"),
    ).reset_index()
    agg["is_incomplete_year"] = agg["year"].isin([2025, 2026])
    for c in ["records", "significant_records", "weighable_records"]:
        agg[c] = agg[c].astype("int32")
    for c in ["region", "subregion", "country", "iso3", "project_group", "unodc_class", "drug"]:
        agg[c] = agg[c].astype("category")
    agg.to_parquet(OUT / "ids_summary.parquet", index=False)
    shutil.copy(ROOT / "data" / "processed" / "signals" / "mena_signals.csv", OUT / "mena_signals.csv")

    # check: the summary must add up to the clean data exactly
    assert agg["records"].sum() == len(df), "record totals do not match"
    assert abs(agg["weight_kg"].sum() - df["weight_kg"].sum()) < 1, "weight totals do not match"
    size = (OUT / "ids_summary.parquet").stat().st_size / 1e6
    print(f"{len(agg):,} summary rows (from {len(df):,} records), {size:.1f} MB -> {OUT}")


if __name__ == "__main__":
    main()
