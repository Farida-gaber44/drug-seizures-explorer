# MENA Early-Warning Signals

**Run:** 2026-10-06 · script `scripts/07_mena_signals.py` · North Africa + Near and Middle East, 17 countries
**Data:** UNODC Drugs Monitoring Platform, Individual Drug Seizures (IDS), records 2011-2025 (2025 incomplete)

## How to read
- **NEW**: first time a drug is recorded in a country (since 2020).
- **RISING**: a drug's share of MENA records grew by 50% or more (2021-22 to 2023-24).
- **SPREADING**: a drug seized in 2 or more additional countries (2019-20 to 2023-24).
- **Confidence** says how likely the signal is real rather than a change in reporting.
  The main trap is a **relabel**: a country starts naming a drug it used to record under a
  vague category (Algeria began recording 'Pregabalin' in 2021 as 'Non-specified psychotropic
  substances' fell from 844 to 40 records), which looks like a new drug but is not.
  Low-confidence signals are kept, because they are worth checking against reports.

## Summary
| signal_type   |   high |   low |   medium |
|:--------------|-------:|------:|---------:|
| NEW           |      4 |    20 |        6 |
| RISING        |      0 |     5 |        1 |
| SPREADING     |      1 |     0 |        4 |

## Rising
| signal_id   | confidence   | summary                                                                                                                                                                 | confidence_reason                                                            |
|:------------|:-------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------|
| S31         | medium       | The share of MDMA in MENA seizure records rose +172% (111 records in 2021-22, 415 in 2023-24), mostly from Algeria (76% of the increase).                               | Algeria accounts for 76% of the rise                                         |
| S32         | low          | The share of Pregabalin in MENA seizure records rose +110% (743 records in 2021-22, 2142 in 2023-24), mostly from Algeria (99% of the increase).                        | Algeria accounts for 99% of the rise and started naming this drug (relabel)  |
| S33         | low          | The share of Cocaine base in MENA seizure records went from zero (0 records in 2021-22, 225 in 2023-24), mostly from Algeria (100% of the increase).                    | Algeria accounts for 100% of the rise and started naming this drug (relabel) |
| S34         | low          | The share of Tramadol in MENA seizure records rose +84% (42 records in 2021-22, 106 in 2023-24), mostly from Algeria (89% of the increase).                             | Algeria accounts for 89% of the rise and started naming this drug (relabel)  |
| S35         | low          | The share of Benzodiazepines in MENA seizure records rose +87% (16 records in 2021-22, 41 in 2023-24), mostly from Algeria (100% of the increase).                      | Algeria accounts for 100% of the rise and started naming this drug (relabel) |
| S36         | low          | The share of Non-specified ecstasy-type substances in MENA seizure records rose +610% (4 records in 2021-22, 39 in 2023-24), mostly from Algeria (83% of the increase). | Algeria accounts for 83% of the rise and started naming this drug (relabel)  |

## Spreading
| signal_id   | confidence   | summary                                                                                                         | confidence_reason                                  |
|:------------|:-------------|:----------------------------------------------------------------------------------------------------------------|:---------------------------------------------------|
| S37         | high         | Non-specified cocaine-type seized in 3 more MENA countries in 2023-24 than in 2019-20: Jordan, Kuwait, Morocco. | 3 new countries (all already reporting in 2019-20) |
| S38         | medium       | Cannabis herb seized in 2 more MENA countries in 2023-24 than in 2019-20: Lebanon, Libya.                       | 2 new countries (all already reporting in 2019-20) |
| S39         | medium       | Other synthetic cannabinoids seized in 2 more MENA countries in 2023-24 than in 2019-20: Egypt, Jordan.         | 2 new countries (all already reporting in 2019-20) |
| S40         | medium       | Diazepam seized in 2 more MENA countries in 2023-24 than in 2019-20: Algeria, Libya.                            | 2 new countries (all already reporting in 2019-20) |
| S41         | medium       | Alprazolam seized in 2 more MENA countries in 2023-24 than in 2019-20: Algeria, Kuwait.                         | 2 new countries (all already reporting in 2019-20) |

## New in a country
| signal_id   | confidence   | summary                                                                                                                                                      | confidence_reason                                                                                                         |
|:------------|:-------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------|
| S01         | high         | Cannabis herb first recorded in Jordan in 2020 (109 records since); already seized in 7 other MENA countries before.                                         | seen in 4 years, no reporting surge                                                                                       |
| S02         | high         | Cannabis herb first recorded in Syrian Arab Republic in 2020 (35 records since); already seized in 7 other MENA countries before.                            | seen in 3 years, no reporting surge                                                                                       |
| S03         | high         | Cannabis herb first recorded in State of Palestine in 2020 (22 records since); already seized in 7 other MENA countries before.                              | seen in 4 years, no reporting surge                                                                                       |
| S04         | high         | MDMA first recorded in Libya in 2020 (10 records since); already seized in 3 other MENA countries before.                                                    | seen in 3 years, no reporting surge                                                                                       |
| S05         | medium       | Pregabalin first recorded in Kuwait in 2023 (11 records since); already seized in 3 other MENA countries before.                                             | no reporting surge, but limited records or years                                                                          |
| S06         | medium       | Methamphetamine first recorded in Egypt in 2020 (8 records since); already seized in 4 other MENA countries before.                                          | no reporting surge, but limited records or years                                                                          |
| S07         | medium       | Non-specified hallucinogens first recorded in Libya in 2020 (8 records since); not seen elsewhere in MENA before.                                            | no reporting surge, but limited records or years                                                                          |
| S08         | medium       | Other synthetic cannabinoids first recorded in Egypt in 2022 (6 records since); not seen elsewhere in MENA before.                                           | no reporting surge, but limited records or years                                                                          |
| S09         | medium       | Diazepam first recorded in Libya in 2021 (6 records since); already seized in 1 other MENA country before.                                                   | no reporting surge, but limited records or years                                                                          |
| S10         | medium       | Cannabis herb first recorded in Lebanon in 2022 (5 records since); already seized in 12 other MENA countries before.                                         | no reporting surge, but limited records or years                                                                          |
| S11         | low          | Pregabalin first recorded in Algeria in 2021 (4063 records since); already seized in 1 other MENA country before.                                            | probable relabel: 'Non-specified psychotropic substances' in Algeria fell from 568 to 202 records a year at the same time |
| S12         | low          | Cocaine base first recorded in Algeria in 2023 (407 records since); not seen elsewhere in MENA before.                                                       | probable relabel: 'Non-specified cocaine-type' in Algeria fell from 106 to 56 records a year at the same time             |
| S13         | low          | Methamphetamine first recorded in Jordan in 2022 (196 records since); already seized in 8 other MENA countries before.                                       | Jordan reported 49.4x its usual number of records that year (possible reporting change)                                   |
| S14         | low          | Tramadol first recorded in Algeria in 2021 (130 records since); already seized in 7 other MENA countries before.                                             | probable relabel: 'Non-specified psychotropic substances' in Algeria fell from 568 to 202 records a year at the same time |
| S15         | low          | Non-specified ecstasy-type substances first recorded in Algeria in 2024 (89 records since); already seized in 5 other MENA countries before.                 | probable relabel: 'Non-specified psychotropic substances' in Algeria fell from 202 to 12 records a year at the same time  |
| S16         | low          | Benzodiazepines first recorded in Algeria in 2021 (80 records since); not seen elsewhere in MENA before.                                                     | probable relabel: 'Non-specified psychotropic substances' in Algeria fell from 568 to 202 records a year at the same time |
| S17         | low          | Other synthetic cannabinoids first recorded in Jordan in 2022 (59 records since); not seen elsewhere in MENA before.                                         | Jordan reported 49.4x its usual number of records that year (possible reporting change)                                   |
| S18         | low          | Fenethylline first recorded in Syrian Arab Republic in 2025 (57 records since, 2025 is incomplete); already seized in 1 other MENA country before.           | Syrian Arab Republic reported 11.7x its usual number of records that year (possible reporting change)                     |
| S19         | low          | Pregabalin first recorded in Syrian Arab Republic in 2025 (52 records since, 2025 is incomplete); already seized in 4 other MENA countries before.           | Syrian Arab Republic reported 11.7x its usual number of records that year (possible reporting change)                     |
| S20         | low          | Methamphetamine first recorded in United Arab Emirates in 2021 (47 records since); already seized in 6 other MENA countries before.                          | United Arab Emirates reported 12.8x its usual number of records that year (possible reporting change)                     |
| S21         | low          | Pregabalin first recorded in United Arab Emirates in 2025 (15 records since, 2025 is incomplete); already seized in 4 other MENA countries before.           | United Arab Emirates reported 7.5x its usual number of records that year (possible reporting change)                      |
| S22         | low          | JWH - 018 first recorded in Jordan in 2025 (14 records since, 2025 is incomplete); not seen elsewhere in MENA before.                                        | probable relabel: 'Other non-specified drugs/substances' in Jordan fell from 52 to 0 records a year at the same time      |
| S23         | low          | Heroin first recorded in Jordan in 2022 (13 records since); already seized in 13 other MENA countries before.                                                | Jordan reported 49.4x its usual number of records that year (possible reporting change)                                   |
| S24         | low          | Tramadol first recorded in Syrian Arab Republic in 2025 (13 records since, 2025 is incomplete); already seized in 9 other MENA countries before.             | Syrian Arab Republic reported 11.7x its usual number of records that year (possible reporting change)                     |
| S25         | low          | Subutex first recorded in Algeria in 2022 (11 records since); already seized in 1 other MENA country before.                                                 | probable relabel: 'Non-specified psychotropic substances' in Algeria fell from 752 to 44 records a year at the same time  |
| S26         | low          | Non-specified synthetic cannabinoids first recorded in Jordan in 2025 (11 records since, 2025 is incomplete); already seized in 1 other MENA country before. | probable relabel: 'Other non-specified drugs/substances' in Jordan fell from 52 to 0 records a year at the same time      |
| S27         | low          | Alprazolam first recorded in Syrian Arab Republic in 2025 (9 records since, 2025 is incomplete); already seized in 4 other MENA countries before.            | Syrian Arab Republic reported 11.7x its usual number of records that year (possible reporting change)                     |
| S28         | low          | Clonazepam first recorded in Morocco in 2020 (6 records since); already seized in 2 other MENA countries before.                                             | seen in one year only, few records                                                                                        |
| S29         | low          | Alprazolam first recorded in United Arab Emirates in 2021 (6 records since); already seized in 1 other MENA country before.                                  | United Arab Emirates reported 12.8x its usual number of records that year (possible reporting change)                     |
| S30         | low          | Cocaine hydrochloride first recorded in Syrian Arab Republic in 2025 (5 records since, 2025 is incomplete); already seized in 3 other MENA countries before. | Syrian Arab Republic reported 11.7x its usual number of records that year (possible reporting change)                     |

## Limits
- Seizures show what was caught and reported, not how much is used or trafficked.
- Algeria provides over half of MENA records, so regional totals lean towards Algeria.
- Egypt reports few records (about 20-30 a year, none after 2023), so Egypt signals are rare.
