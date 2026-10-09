# Cleaning Log

**Run:** 2026-10-05 · script `scripts/04_clean.py` · decisions from `reports/01_quality_check_summary.md`
**Output:** `data/processed/ids_clean.parquet`, 2,841,288 rows (same as raw: no rows deleted, problems are flagged)

## What was done
| Step | Result |
|---|---|
| Subregion spellings merged | Subregion names merged: 22 -> 17 |
| Month and quarter added | from the real seizure date |
| Drug class added | `unodc_class` and `project_group` from `data/reference/drug_class_lookup.csv` (343 names, 185 classified by hand) |
| Weight in kg | `weight_kg` for g/kg rows: 2,629,269 rows (92.5%) |
| Zero or negative quantity flagged | `is_invalid_quantity`: 142 rows (excluded from weight) |
| Weight outliers flagged (one seizure ≥ 1,000,000 kg) | `is_weight_outlier`: 2 rows (excluded from weight) |
| Exact duplicates within a year flagged | `is_duplicate`: 239,664 rows (8.4%), kept by default |
| UNODC "significant seizure" flag | `is_significant`: 620,741 rows (21.8%); cannabis/opium ≥ 1 kg, other drugs ≥ 100 g, NPS any amount; non-g/kg rows = False |
| Incomplete years flagged | `is_incomplete_year`: 2025 and 2026, 106,518 rows |
| Columns dropped | seizure_location, transport_mode, source, reporting_channel, source_sheet |

- Country names: 149 -> 147 (one name per ISO3)
- City names: 79,049 spellings -> 71,918 city keys
- Dropped `source`: values {'Government': 2841288}
- Dropped `reporting_channel`: values {'Individual Drug Seizures (IDS)': 2841288}

## Weight outliers
|   year | country   | city    | drug        |   quantity | unit   |
|-------:|:----------|:--------|:------------|-----------:|:-------|
|   2013 | Thailand  | Bangkok | Amphetamine |    4.5e+06 | kg     |
|   2013 | Thailand  | Bangkok | Amphetamine |    4.5e+06 | kg     |

## Rows by project group
| project_group               |    rows |   weight_kg | share_rows   |
|:----------------------------|--------:|------------:|:-------------|
| New psychoactive substances |   64751 |     160,838 | 2.3%         |
| Other / unspecified         |   58790 |     164,948 | 2.1%         |
| Pharmaceutical              |   96763 |   1,043,427 | 3.4%         |
| Plant-based                 | 2371813 |  44,366,358 | 83.5%        |
| Precursors & chemicals      |    6838 |     945,258 | 0.2%         |
| Synthetic                   |  242333 |     511,835 | 8.5%         |

## How to use the flags
- **Records (case counts):** use all rows; for a robustness check also run with `is_duplicate == False`.
- **Same rule for every country and year:** filter `is_significant == True` (countries differ in whether they report small seizures, and reporting changed around 2014).
- **City maps:** group by `iso3` + `city_key` (original `city` kept for labels).
- **Sharing:** publish aggregated tables only; UNODC asks that individual seizure records are not redistributed.
- **Weight:** use `weight_kg` (already excludes invalid and outlier rows).
- **Trends:** show 2025 and 2026 separately or marked as incomplete.
