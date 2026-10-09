"""Drug x year summaries showing both measures side by side: number of records and weight.

Reads the cleaned data (run 04_clean.py first).
- cases: every seizure record, whatever its unit (tablets, plants, litres included).
- total_kg: `weight_kg` from the clean data (g/kg rows only, invalid and outlier rows excluded).
  weighable_share shows how much of the records the weight figure covers.
- rank_by_cases / rank_by_weight: position within the year under each measure,
  so it is clear when the two measures disagree.
Outputs one CSV per level (drug, UNODC class, project group) for the analysis and Power BI.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def summarise(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    out = df.groupby(keys).agg(
        cases=("case_id", "size"),
        countries=("country", "nunique"),
        weighable_cases=("is_weighable", "sum"),
        total_kg=("weight_kg", "sum"),
        median_g=("weight_kg", lambda s: s.median() * 1000 if s.notna().any() else float("nan")),
        max_kg=("weight_kg", "max"),
    ).reset_index()
    out["weighable_share"] = out["weighable_cases"] / out["cases"]

    year_totals = out.groupby("year")[["cases", "total_kg"]].transform("sum")
    out["share_of_year_cases"] = out["cases"] / year_totals["cases"]
    out["share_of_year_kg"] = out["total_kg"] / year_totals["total_kg"]
    out["rank_by_cases"] = out.groupby("year")["cases"].rank(ascending=False, method="min").astype(int)
    out["rank_by_weight"] = out.groupby("year")["total_kg"].rank(ascending=False, method="min").astype(int)
    out["larger_measure"] = "same rank"
    out.loc[out["rank_by_cases"] < out["rank_by_weight"], "larger_measure"] = "ranks higher by cases"
    out.loc[out["rank_by_cases"] > out["rank_by_weight"], "larger_measure"] = "ranks higher by weight"
    out["is_incomplete_year"] = out["year"].isin([2025, 2026])
    return out


def main() -> None:
    df = pd.read_parquet(PROCESSED / "ids_clean.parquet", columns=[
        "case_id", "year", "country", "drug", "unodc_class", "project_group", "weight_kg", "is_weighable"])

    levels = {
        "drug_year_summary.csv": ["year", "project_group", "unodc_class", "drug"],
        "drug_class_year_summary.csv": ["year", "unodc_class"],
        "project_group_year_summary.csv": ["year", "project_group"],
    }
    results = {}
    for name, keys in levels.items():
        results[name] = summarise(df, keys)
        results[name].to_csv(PROCESSED / name, index=False, encoding="utf-8")
        print(f"Saved {name}: {len(results[name]):,} rows")

    groups = results["project_group_year_summary.csv"]
    pd.set_option("display.width", 220)
    cols = ["project_group", "cases", "share_of_year_cases", "total_kg", "share_of_year_kg",
            "rank_by_cases", "rank_by_weight"]
    for year in (2013, 2015, 2020, 2024):
        t = groups[groups["year"] == year].sort_values("cases", ascending=False)[cols]
        print(f"\n=== {year} by project group")
        print(t.to_string(index=False, formatters={
            "share_of_year_cases": "{:.1%}".format, "share_of_year_kg": "{:.1%}".format,
            "total_kg": "{:,.0f}".format, "cases": "{:,}".format}))


if __name__ == "__main__":
    main()
