# Data Quality Check: UNODC Individual Drug Seizures (IDS)

**Source:** UNODC Drugs Monitoring Platform (dmp.unodc.org/downloadIDS), files `IDS-data-2011_17-May24.xlsx`, `IDS-data-2018-2022.xlsx`, `IDS-data-2023-2026-V1.xlsx`
**Checked:** 2026-10-04, script `scripts/02_profile.py`, full output in `reports/01_quality_check_output.txt`
**Size:** 2,841,288 rows · 150 countries · 343 drug names · 2011 to June 2026

## Key findings

| # | Finding | Impact | Decision (proposed) |
|---|---|---|---|
| 1 | **Dates are real**: 365 to 366 different dates per year (2026 ends on 30 June) | Monthly and seasonal analysis is possible | Keep the date; add month and quarter columns |
| 2 | **Reporting countries vary a lot**: from 45 (2015) to 100 (2023); 2025 has 64 and 2026 has 32 | Raw totals across years are misleading | Use shares; give each country equal weight; test only consistent reporters; mark 2025 and 2026 as incomplete |
| 3 | **Colombia dominates 2014 to 2016** (about 70 to 90% of rows) | Case-count shares for those years mostly reflect Colombia | Equal-country weighting; show results with and without Colombia |
| 4 | **8.4% exact duplicate rows within the same year** (15 to 17% in 2014 to 2016) | Some may be real repeated small seizures (same city, drug, date, amount) | Keep by default; flag `is_duplicate`; test the results with them removed |
| 5 | **Obvious error: Thailand 2013, Amphetamine, 4,500,000 kg, listed twice** (4,500 tonnes) | Makes up 82% of all 2013 seizure weight | Flag as an outlier and leave it out of weight totals |
| 6 | **A few huge seizures drive weight totals** (top 10 seizures = 15 to 29% of yearly weight in many years) | Weight trends jump around | Show median weight and the number of records next to total weight |
| 7 | **Subregion names are spelled differently in different files** (e.g. "West and Central Europe" vs "Western and Central Europe"; "East Europe" vs "Eastern Europe"; "South West Asia" vs "South-West Asia") | Splits one subregion into two | Merge into one standard name per subregion |
| 8 | **Units**: kg 61.5%, g 31.1% (92.6% can be weighed); tablets 2.9%, units 3.2%, plants 0.7%, litres 0.7% | Weight leaves out pill-based drugs (captagon, ecstasy) | Use both measures: records (all units) and weight (g/kg only) |
| 9 | **142 rows with zero or negative quantity** | Invalid amounts | Exclude from weight; keep in record counts |
| 10 | **Mostly empty columns**: seizure location 67% empty, transport mode 89% empty | Not usable for trends | Drop from the main analysis |
| 11 | **185 drug names (7,230 rows) not in UNODC's official drug list** (e.g. "Other synthetic cathinones", "5F-AKB48", "GHB/GBL", "Cannabis Leaves") | Would be left without a class | Map them by hand in the drug-class lookup |
| 12 | **Egypt: 160 rows in 6 years** (2013, 2018, and 2020 to 2023; 20 to 32 rows per year), mostly hashish, heroin, tramadol, captagon | Too little for an Egypt-only project | Egypt as a small, clearly labelled panel inside North Africa / Near and Middle East |
| 13 | **2023 vs 2024 are not copies**: 354,923 vs 184,464 rows, 100 vs 85 countries; 21.8% matching rows, which is close to the normal level for consecutive years | No action needed | The sheet sizes stored inside the Excel file are wrong; always count the rows |

## Region structure (for the Middle East / North Africa view)
- **North Africa** (region: Africa), 22,639 rows
- **Near and Middle East** (region: Asia), 5,974 rows
- Together they form the MENA view.

## Next step
Approve the proposed decisions, then `scripts/04_clean.py` creates `data/processed/ids_clean.parquet`.
