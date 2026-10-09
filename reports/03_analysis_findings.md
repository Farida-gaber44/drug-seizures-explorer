# Analysis Findings: From plants to labs

**Run:** 2026-10-05 · script `scripts/05_analysis.py` · data `data/processed/ids_clean.parquet`
**Base for shares:** the four drug groups (plant-based, synthetic, pharmaceutical, new psychoactive substances).
**Lab-made** = synthetic + new psychoactive substances.

## 1. Lab-made share of seizures, world, five methods
| Measure | Method | 2012 | 2016 | 2020 | 2024 |
|---|---|---|---|---|---|
| records | pooled | 7.1% | 2.8% | 18.2% | 18.1% |
| records | pooled_no_col | 11.3% | 8.9% | 27.2% | 22.6% |
| records | country_avg | 14.5% | 22.0% | 24.2% | 23.7% |
| records | consistent_panel | 9.7% | 22.6% | 20.4% | 23.7% |
| records | significant_only | 16.4% | 22.6% | 22.9% | 25.9% |
| weight | pooled | 1.3% | 1.2% | 1.6% | 3.2% |
| weight | pooled_no_col | 1.9% | 3.2% | 2.4% | 4.2% |
| weight | country_avg | 8.1% | 10.5% | 10.3% | 11.0% |
| weight | consistent_panel | 2.7% | 9.7% | 6.4% | 10.4% |
| weight | significant_only | 8.8% | 11.5% | 9.6% | 11.3% |

- **pooled**: all rows added up · **pooled_no_col**: without Colombia
- **country_avg**: each country counts equally (country-years with ≥ 20 records)
- **consistent_panel**: country_avg for the 27 countries reporting in ≥ 10 of the 14 complete years:
  Austria, Bulgaria, China, Macao SAR, Colombia, Croatia, Cyprus, Czechia, Denmark, El Salvador, Guatemala, India, Italy, Kazakhstan, Luxembourg, Malta, Pakistan, Peru, Portugal, Romania, Russian Federation, Serbia, Spain, Switzerland, Syrian Arab Republic, Ukraine, Uzbekistan, Venezuela (Bolivarian Republic of)
- **significant_only**: country_avg using only seizures meeting UNODC's thresholds (cannabis/opium ≥ 1 kg,
  other drugs ≥ 100 g, NPS any amount; tablets and other non-g/kg rows excluded, which is conservative for lab-made drugs)

## 2. Lab-made share by region (records, every country counts equally)
| region   | 2012   | 2016   | 2020   | 2024   |
|:---------|:-------|:-------|:-------|:-------|
| Africa   | 13%    | 0%     | 9%     | 12%    |
| Americas | 2%     | 0%     | 13%    | 5%     |
| Asia     | 27%    | 26%    | 29%    | 46%    |
| Europe   | 15%    | 31%    | 29%    | 27%    |
| Oceania  | 15%    | 33%    | 60%    | –      |

## 3. Middle East and North Africa (records, all rows added up)
Lab-made share:
| subregion            | 2018   | 2019   | 2020   | 2021   | 2022   | 2023   | 2024   | 2025   | 2026   |
|:---------------------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|
| Near and Middle East | 35%    | 55%    | 29%    | 37%    | 60%    | 47%    | 54%    | 57%    | 75%    |
| North Africa         | 2%     | 1%     | 3%     | 3%     | 4%     | 9%     | 9%     | 6%     | 5%     |

Records per year (small numbers mean unstable shares):
| subregion            |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |   2025 |   2026 |
|:---------------------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| Near and Middle East |    263 |    137 |    507 |    248 |   1036 |    426 |    911 |   1437 |    353 |
| North Africa         |    696 |    665 |   1062 |   1336 |   2201 |   2666 |   2602 |   3085 |    860 |

Top 5 drugs since 2020:
| subregion            | drug                       |   records |
|:---------------------|:---------------------------|----------:|
| Near and Middle East | Captagon                   |      1795 |
| Near and Middle East | Cannabis resin (hashish)   |      1365 |
| Near and Middle East | Methamphetamine            |       616 |
| Near and Middle East | Cannabis herb (marijuana)  |       407 |
| Near and Middle East | Pregabalin                 |       111 |
| North Africa         | Cannabis resin (hashish)   |      4986 |
| North Africa         | Pregabalin                 |      4386 |
| North Africa         | Non-specified cocaine-type |       815 |
| North Africa         | Cannabis herb (marijuana)  |       707 |
| North Africa         | MDMA                       |       677 |

## 4. Drug-mix concentration (HHI, by records; 1 = a single drug, lower = more diverse)
| region   |   2012 |   2016 |   2020 | 2024   |
|:---------|-------:|-------:|-------:|:-------|
| Africa   |   0.4  |   0.33 |   0.26 | 0.18   |
| Americas |   0.37 |   0.39 |   0.15 | 0.17   |
| Asia     |   0.26 |   0.18 |   0.12 | 0.41   |
| Europe   |   0.15 |   0.22 |   0.15 | 0.17   |
| Oceania  |   0.28 |   0.41 |   0.14 | –      |

## Notes
- 2025 and 2026 are incomplete (late reporting); they are in the CSVs, flagged, and not used above.
- 2024 pharmaceutical weight is driven by large Nigerian codeine seizures at Tin Can port (Lagos).
- The consistent panel is mostly European, so it tests the reporting effect but does not represent the world.
- Seizures reflect enforcement and reporting, not the size of drug markets.
