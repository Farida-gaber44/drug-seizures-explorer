"""Core analysis: has the seized drug mix shifted from plant-based to lab-made drugs?

Every share is shown under both measures (records and weight) and four ways, so the reader can
see whether the shift is real or created by who reports:
  pooled            all rows added up (dominated by big reporters such as Colombia)
  pooled_no_col     same, without Colombia
  country_avg       each country's mix computed first, then averaged (every country counts equally)
  consistent_panel  country_avg restricted to countries that reported in most years
  significant_only  country_avg using only seizures above UNODC's "significant" thresholds,
                    so every country and year follows the same reporting rule

Shares use the four drug groups only (precursors/chemicals and 'other/unspecified' are excluded
from the base). Country-years with fewer than MIN_RECORDS records are skipped in country averages.

Input:  data/processed/ids_clean.parquet
Output: data/processed/analysis/*.csv, reports/03_analysis_findings.md
"""
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "analysis"
DRUG_GROUPS = ["Plant-based", "Synthetic", "Pharmaceutical", "New psychoactive substances"]
LAB_GROUPS = ["Synthetic", "New psychoactive substances"]
MIN_RECORDS = 20
COMPLETE_YEARS = range(2011, 2025)
PANEL_MIN_YEARS = 10
MENA = ["North Africa", "Near and Middle East"]
MEASURES = {"records": "case_id", "weight": "weight_kg"}


def group_totals(df, keys, measure):
    col = MEASURES[measure]
    agg = "size" if measure == "records" else "sum"
    t = df.groupby(keys + ["project_group"])[col].agg(agg).unstack("project_group", fill_value=0)
    return t.reindex(columns=DRUG_GROUPS, fill_value=0)


def shares(totals):
    s = totals.div(totals.sum(axis=1), axis=0)
    s["Lab-made (synthetic + NPS)"] = s[LAB_GROUPS].sum(axis=1)
    return s


def mix(df, keys, measure, method, panel=None):
    """Drug-group shares per `keys` (which must include 'year') using one of the four methods."""
    if method == "pooled_no_col":
        df = df[df["country"] != "Colombia"]
    if method in ("pooled", "pooled_no_col"):
        return shares(group_totals(df, keys, measure))
    if method == "consistent_panel":
        df = df[df["country"].isin(panel)]
    if method == "significant_only":
        df = df[df["is_significant"]]
    counts = df.groupby(["country", "year"]).size()
    keep = counts[counts >= MIN_RECORDS].index
    df = df.set_index(["country", "year"]).loc[lambda d: d.index.isin(keep)].reset_index()
    per_country = shares(group_totals(df, keys + ["country"], measure)).dropna()
    return per_country.groupby(level=keys).mean()


def hhi(df, keys):
    """Herfindahl index of the drug mix (by records, individual drug names): 1 = one drug only."""
    s = df.groupby(keys + ["drug"]).size()
    s = s / s.groupby(level=keys).transform("sum")
    return (s ** 2).groupby(level=keys).sum().rename("hhi")


def to_long(frames):
    rows = []
    for (measure, method), s in frames.items():
        t = s.reset_index().melt(id_vars=s.index.names, var_name="project_group", value_name="share")
        rows.append(t.assign(measure=measure, method=method))
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(ROOT / "data" / "processed" / "ids_clean.parquet")
    df = df[df["project_group"].isin(DRUG_GROUPS)]

    years = df[df["year"].isin(COMPLETE_YEARS)].groupby(["country", "year"]).size()
    years = years[years >= MIN_RECORDS].reset_index().groupby("country")["year"].nunique()
    panel = sorted(years[years >= PANEL_MIN_YEARS].index)
    pd.Series(panel, name="country").to_csv(OUT / "consistent_reporters.csv", index=False)

    methods = ["pooled", "pooled_no_col", "country_avg", "consistent_panel", "significant_only"]
    world = {(m, meth): mix(df, ["year"], m, meth, panel) for m in MEASURES for meth in methods}
    world_long = to_long(world)
    world_long["is_incomplete_year"] = world_long["year"].isin([2025, 2026])
    world_long.to_csv(OUT / "world_mix_by_method.csv", index=False)

    region = {(m, "country_avg"): mix(df, ["region", "year"], m, "country_avg") for m in MEASURES}
    region.update({(m, "pooled"): mix(df, ["region", "year"], m, "pooled") for m in MEASURES})
    to_long(region).to_csv(OUT / "region_mix.csv", index=False)

    mena = df[df["subregion"].isin(MENA)]
    mena_mix = {(m, "pooled"): mix(mena, ["subregion", "year"], m, "pooled") for m in MEASURES}
    to_long(mena_mix).to_csv(OUT / "mena_mix.csv", index=False)
    mena_drugs = mena.groupby(["subregion", "year", "drug"]).agg(
        records=("case_id", "size"), weight_kg=("weight_kg", "sum"), countries=("country", "nunique")).reset_index()
    mena_drugs.to_csv(OUT / "mena_top_drugs.csv", index=False)
    egypt = df[df["country"] == "Egypt"].groupby(["year", "drug"]).agg(
        records=("case_id", "size"), weight_kg=("weight_kg", "sum")).reset_index()
    egypt.to_csv(OUT / "egypt_detail.csv", index=False)

    region_hhi = hhi(df, ["region", "year"]).reset_index()
    region_hhi.to_csv(OUT / "region_diversity_hhi.csv", index=False)

    # ---------- findings report ----------
    lab = "Lab-made (synthetic + NPS)"
    def lab_row(measure, method, y):
        s = world[(measure, method)]
        return s.loc[y, lab] if y in s.index else float("nan")

    compare_years = [2012, 2016, 2020, 2024]
    lines = []
    for measure in MEASURES:
        for meth in methods:
            vals = " | ".join(f"{lab_row(measure, meth, y):.1%}" for y in compare_years)
            lines.append(f"| {measure} | {meth} | {vals} |")

    reg = region[("records", "country_avg")][lab].unstack("year")
    reg_txt = reg.reindex(columns=compare_years).map(lambda v: f"{v:.0%}" if pd.notna(v) else "–")

    mena_lab = mena_mix[("records", "pooled")][lab].unstack("year").reindex(columns=range(2018, 2027))
    mena_txt = mena_lab.map(lambda v: f"{v:.0%}" if pd.notna(v) else "–")
    mena_counts = mena.groupby(["subregion", "year"]).size().unstack("year").reindex(columns=range(2018, 2027))

    top_mena = (mena[mena["year"] >= 2020].groupby(["subregion", "drug"]).size()
                .groupby(level=0, group_keys=False).nlargest(5).rename("records").reset_index())
    hhi_txt = region_hhi.pivot(index="region", columns="year", values="hhi").reindex(
        columns=compare_years).map(lambda v: f"{v:.2f}" if pd.notna(v) else "–")

    report = f"""# Analysis Findings: From plants to labs

**Run:** {date.today()} · script `scripts/05_analysis.py` · data `data/processed/ids_clean.parquet`
**Base for shares:** the four drug groups (plant-based, synthetic, pharmaceutical, new psychoactive substances).
**Lab-made** = synthetic + new psychoactive substances.

## 1. Lab-made share of seizures, world, five methods
| Measure | Method | 2012 | 2016 | 2020 | 2024 |
|---|---|---|---|---|---|
{chr(10).join(lines)}

- **pooled**: all rows added up · **pooled_no_col**: without Colombia
- **country_avg**: each country counts equally (country-years with ≥ {MIN_RECORDS} records)
- **consistent_panel**: country_avg for the {len(panel)} countries reporting in ≥ {PANEL_MIN_YEARS} of the 14 complete years:
  {', '.join(panel)}
- **significant_only**: country_avg using only seizures meeting UNODC's thresholds (cannabis/opium ≥ 1 kg,
  other drugs ≥ 100 g, NPS any amount; tablets and other non-g/kg rows excluded, which is conservative for lab-made drugs)

## 2. Lab-made share by region (records, every country counts equally)
{reg_txt.to_markdown()}

## 3. Middle East and North Africa (records, all rows added up)
Lab-made share:
{mena_txt.to_markdown()}

Records per year (small numbers mean unstable shares):
{mena_counts.fillna(0).astype(int).to_markdown()}

Top 5 drugs since 2020:
{top_mena.to_markdown(index=False)}

## 4. Drug-mix concentration (HHI, by records; 1 = a single drug, lower = more diverse)
{hhi_txt.to_markdown()}

## Notes
- 2025 and 2026 are incomplete (late reporting); they are in the CSVs, flagged, and not used above.
- 2024 pharmaceutical weight is driven by large Nigerian codeine seizures at Tin Can port (Lagos).
- The consistent panel is mostly European, so it tests the reporting effect but does not represent the world.
- Seizures reflect enforcement and reporting, not the size of drug markets.
"""
    (ROOT / "reports" / "03_analysis_findings.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
