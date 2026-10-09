# Report library coverage of MENA signals

**Run:** 2026-10-06 · script `scripts/10_doc_coverage.py` · 1,192 report pages, 11 reports used
**Method:** keyword search. *Strong* = a page names both the drug and the country (or MENA for region-wide
signals); *weak* = the drug is mentioned but never with that place; *none* = drug not mentioned.
A match means relevant text exists; it does not prove the text explains the signal.

## Coverage by signal confidence
| confidence   |   strong |   weak |   none |
|:-------------|---------:|-------:|-------:|
| high         |        4 |      1 |      0 |
| medium       |       10 |      1 |      0 |
| low          |       23 |      2 |      0 |

**Total:** 37 of 41 signals strong, 4 weak, 0 none.

## Stricter check: drug and place in the same paragraph (within 300 characters)
**27 of 41 signals** have such a passage. By confidence:
high 4 of 5, medium 7 of 11, low 16 of 25.
This is the better guide to what the assistant can explain with a direct citation.

## Most useful reports (signals with a strong match)
| doc_id                    |   signals_with_strong_match | title                                                                          |
|:--------------------------|----------------------------:|:-------------------------------------------------------------------------------|
| incb_ar_2024              |                          19 | Report of the International Narcotics Control Board for 2024                   |
| incb_ar_2022              |                          15 | Report of the International Narcotics Control Board for 2022                   |
| incb_ar_2023              |                          15 | Report of the International Narcotics Control Board for 2023                   |
| incb_ar_2021              |                          13 | Report of the International Narcotics Control Board for 2021                   |
| unodc_synthetic_2020      |                          11 | Global Synthetic Drugs Assessment 2020                                         |
| wdr2026_highlights        |                           7 | World Drug Report 2026: Highlights                                             |
| incb_ar_2025              |                           6 | Report of the International Narcotics Control Board for 2025                   |
| unodc_nauss_captagon_2025 |                           4 | Research brief: changes in synthetic drug markets in Arab countries (captagon) |
| emcdda_captagon_2018      |                           4 | Captagon: understanding today's illicit market                                 |
| wdr2025_key_findings      |                           3 | World Drug Report 2025: Key findings                                           |
| wdr2024_key_findings      |                           2 | World Drug Report 2024: Key findings and conclusions                           |

## Signals without a same-paragraph match (gaps)
| signal_id   | confidence   | country              | drug                                         | coverage   |
|:------------|:-------------|:---------------------|:---------------------------------------------|:-----------|
| S03         | high         | State of Palestine   | Cannabis herb (marijuana)                    | weak       |
| S05         | medium       | Kuwait               | Pregabalin                                   | strong     |
| S07         | medium       | Libya                | Non-specified hallucinogens                  | weak       |
| S08         | medium       | Egypt                | Other synthetic cannabinoids (spice)         | strong     |
| S09         | medium       | Libya                | Diazepam                                     | strong     |
| S15         | low          | Algeria              | Non-specified ecstasy-type substances        | strong     |
| S16         | low          | Algeria              | Benzodiazepines                              | strong     |
| S17         | low          | Jordan               | Other synthetic cannabinoids (spice)         | strong     |
| S19         | low          | Syrian Arab Republic | Pregabalin                                   | strong     |
| S21         | low          | United Arab Emirates | Pregabalin                                   | strong     |
| S22         | low          | Jordan               | JWH - 018                                    | strong     |
| S26         | low          | Jordan               | Non-specified synthetic cannabinoids (spice) | strong     |
| S27         | low          | Syrian Arab Republic | Alprazolam (Xanax, Pranax, Ksalol)           | weak       |
| S29         | low          | United Arab Emirates | Alprazolam (Xanax, Pranax, Ksalol)           | weak       |

Full table: `data/docs/signal_coverage.csv`.
