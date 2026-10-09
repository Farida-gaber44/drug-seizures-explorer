"""Profile the combined IDS data before cleaning. Prints facts only; changes nothing."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_parquet(ROOT / "data" / "interim" / "ids_raw.parquet")
CASE_COLS = ["seizure_date", "country", "city", "admin_region", "drug", "unit", "quantity",
             "seizure_location", "transport_mode"]
pd.set_option("display.width", 200, "display.max_rows", 200)


def section(title):
    print(f"\n===== {title}")


section("Size")
print(f"{len(df):,} rows, {df['country'].nunique()} countries, {df['drug'].nunique()} drug names")

section("Rows and reporting countries per year")
print(df.groupby("year").agg(rows=("drug", "size"), countries=("country", "nunique")))

section("Distinct seizure dates per year (are dates real or year placeholders?)")
print(df.groupby("year")["seizure_date"].agg(["nunique", "min", "max"]))

section("Is the 2024 sheet a copy of 2023?")
a = df[df.year == 2023][CASE_COLS[1:]].reset_index(drop=True)
b = df[df.year == 2024][CASE_COLS[1:]].reset_index(drop=True)
print(f"2023 rows {len(a):,}, 2024 rows {len(b):,}")
if len(a) == len(b):
    print(f"identical row by row (ignoring date): {a.equals(b)}")
print("countries 2023:", a["country"].nunique(), "| 2024:", b["country"].nunique())
print("top countries 2023:", a["country"].value_counts().head(5).to_dict())
print("top countries 2024:", b["country"].value_counts().head(5).to_dict())

section("Exact duplicate rows within the same year")
dup = df.duplicated(subset=CASE_COLS + ["year"], keep="first")
print(f"{dup.sum():,} duplicate rows ({dup.mean():.1%})")
print(dup.groupby(df["year"]).mean().map("{:.1%}".format).to_dict())

section("Measurement units")
print(df["unit"].value_counts(dropna=False).to_frame("rows").assign(share=lambda t: (t.rows / len(df)).map("{:.1%}".format)))

section("Missing / 'Data not available' per column")
na = df.isna() | df.isin(["", "Data not available", "nan"])
print(na.mean().map("{:.0%}".format))

section("Quantity problems")
print(f"non-numeric or missing: {df['quantity'].isna().sum():,} | zero or negative: {(df['quantity'] <= 0).sum():,}")

section("Largest single seizures by weight (possible typos or real record seizures)")
w = df[df["unit"].isin(["kg", "g"])].assign(kg=lambda t: t["quantity"] * t["unit"].map({"kg": 1, "g": 0.001}))
print(w.nlargest(20, "kg")[["year", "country", "city", "drug", "quantity", "unit", "kg"]].to_string(index=False))
print("\nShare of each year's total weight coming from its 10 largest seizures:")
top10 = w.groupby("year")["kg"].apply(lambda s: s.nlargest(10).sum() / s.sum())
print(top10.map("{:.0%}".format).to_string())

section("Region and subregion labels")
print(df.groupby(["region", "subregion"]).size().to_string())

section("Egypt")
eg = df[df["country"].str.contains("Egypt", na=False)]
print(f"{len(eg):,} rows")
print(eg.groupby("year").size().to_string())
print(eg["drug"].value_counts().head(10).to_string())
print(eg["unit"].value_counts().to_string())

section("Drug names not in UNODC drug list")
drug_list = pd.read_csv(ROOT / "data" / "interim" / "unodc_drug_list.csv")
missing = df.loc[~df["drug"].isin(drug_list["drug"]), "drug"].value_counts()
print(f"{missing.sum():,} rows across {len(missing)} names")
print(missing.head(30).to_string())
