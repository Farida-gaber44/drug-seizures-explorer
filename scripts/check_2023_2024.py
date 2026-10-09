from pathlib import Path

import pandas as pd

# Path built from this file's location, so it works from any folder
f = Path(__file__).resolve().parents[1] / "data" / "raw" / "IDS-data-2023-2026-V1.xlsx"
a = pd.read_excel(f, sheet_name="2023", dtype=str)
b = pd.read_excel(f, sheet_name="2024", dtype=str)

cols = [c for c in a.columns if c != "Seizure Date"]  # dates differ by design
print("Rows 2023:", len(a), "| Rows 2024:", len(b))
print("Countries 2023:", a["Country/Territory of Seizure"].nunique(),
      "| 2024:", b["Country/Territory of Seizure"].nunique())

# Same rows, ignoring order?
sa = a[cols].sort_values(cols).reset_index(drop=True)
sb = b[cols].sort_values(cols).reset_index(drop=True)
print("Identical content (ignoring order):", sa.equals(sb))

# How many rows of 2024 also appear in 2023?
m = b[cols].merge(a[cols].drop_duplicates(), how="inner")
print(f"2024 rows also found in 2023: {len(m):,} ({len(m)/len(b):.1%})")