"""Early-warning signals for drug seizures in the Middle East and North Africa (MENA).

Three signal types, each with a confidence level and a plain-English sentence:
  NEW        a drug recorded for the first time in a country (since 2020), in a country that
             was already reporting in at least 2 earlier years
  RISING     a drug's share of MENA seizure records grew >= 50% (2023-24 vs 2021-22)
  SPREADING  a drug seized in at least 2 more MENA countries (2023-24 vs 2019-20)

Confidence guards against reporting artifacts, which look like real change:
  relabel    a country starts naming a drug it used to file under a vague category
             (e.g. Algeria: 'Non-specified psychotropic substances' -> 'Pregabalin' in 2021)
  surge      a country suddenly reports many more records overall
  NEW:       low if relabel or surge (> 3x usual records), or one year with < 10 records
  RISING:    high if >= 2 countries drive the rise and no single country is > 70% of it;
             low if the main driver is a relabel
  SPREADING: only countries already reporting in 2019-20 count; relabels do not count;
             high if >= 3 new countries
2025 is incomplete: NEW signals from 2025 are marked 'early'. 2026 is not used.
Shares use records (counts); vague names ('Other non-specified ...') are left out.

Input:  data/processed/ids_clean.parquet
Output: data/processed/signals/mena_signals.csv, reports/04_mena_signals.md
"""
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MENA = ["North Africa", "Near and Middle East"]
DRUG_GROUPS = ["Plant-based", "Synthetic", "Pharmaceutical", "New psychoactive substances"]
VAGUE = {"Other non-specified drugs/substances", "Other-miscellaneous", "Other drugs/substances",
         "Non-specified synthetic drugs/substances", "Non-specified psychotropic substances"}
LAST_YEAR, EARLY_YEAR = 2024, 2025
BASE, RECENT, SPREAD_BASE = [2021, 2022], [2023, 2024], [2019, 2020]
NEW_FROM, MIN_PRIOR_YEARS, MIN_NEW_RECORDS = 2020, 2, 5
RISE_MIN_RECORDS, RISE_MIN_CHANGE = 30, 0.5
SURGE_RATIO, DOMINANT_SHARE, RELABEL_DROP = 3.0, 0.7, 0.4


def short(drug):
    return drug.split(" (")[0]


def load():
    df = pd.read_parquet(ROOT / "data" / "processed" / "ids_clean.parquet",
                         columns=["year", "subregion", "country", "drug", "unodc_class", "project_group", "case_id"])
    df = df[df["subregion"].isin(MENA) & (df["year"] <= EARLY_YEAR)]
    totals = df.groupby(["country", "year"]).size()            # all records: reporting volume
    drugs = df[df["project_group"].isin(DRUG_GROUPS) & ~df["drug"].isin(VAGUE)]
    return drugs, totals, df


def is_vague(drug):
    return drug in VAGUE or drug.startswith(("Non-specified", "Other"))


GENERAL_VAGUE_CLASSES = {"Non-specified psychotropic substances", "Other drugs/substances"}


def relabel_source(all_rows, country, drug, year):
    """Vague category of the same drug family in the same country whose records fell >= 40%
    when `drug` first appeared. Family = same UNODC class, or a general catch-all category."""
    c = all_rows[all_rows["country"] == country]
    drug_class, group = c.loc[c["drug"] == drug, ["unodc_class", "project_group"]].iloc[0]
    general = GENERAL_VAGUE_CLASSES if group != "Plant-based" else {"Other drugs/substances"}
    vague_rows = c[c["drug"].map(is_vague) & (c["drug"] != drug)]
    same_family = list(vague_rows.loc[vague_rows["unodc_class"] == drug_class, "drug"].unique())
    catch_all = list(vague_rows.loc[vague_rows["unodc_class"].isin(general), "drug"].unique())
    for vague in same_family + [d for d in catch_all if d not in same_family]:   # own family first
        n = c[c["drug"] == vague].groupby("year").size()
        before = n.reindex([year - 2, year - 1], fill_value=0).mean()
        after = n.reindex([year + 1, year + 2], fill_value=0).mean()
        if before >= 20 and after <= before * (1 - RELABEL_DROP):
            return vague, before, after
    return None


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def new_signals(df, totals, all_rows):
    g = df.groupby(["country", "drug", "project_group"]).agg(
        first_year=("year", "min"), records=("case_id", "size"), years_seen=("year", "nunique")).reset_index()
    rows = []
    for r in g[g["first_year"] >= NEW_FROM].itertuples():
        country_years = totals.loc[r.country]
        prior = country_years[country_years.index < r.first_year]
        if len(prior) < MIN_PRIOR_YEARS or r.records < MIN_NEW_RECORDS:
            continue
        surge = country_years.loc[r.first_year] / prior.median()
        elsewhere = df[(df["drug"] == r.drug) & (df["country"] != r.country)
                       & (df["year"] < r.first_year)]["country"].nunique()
        relabel = relabel_source(all_rows, r.country, r.drug, r.first_year)
        if relabel:
            vague, before, after = relabel
            conf, why = "low", (f"probable relabel: '{short(vague)}' in {r.country} fell from "
                                f"{before:.0f} to {after:.0f} records a year at the same time")
        elif surge > SURGE_RATIO:
            conf, why = "low", f"{r.country} reported {surge:.1f}x its usual number of records that year (possible reporting change)"
        elif r.years_seen == 1 and r.records < 10:
            conf, why = "low", "seen in one year only, few records"
        elif r.years_seen >= 2 and r.records >= 10:
            conf, why = "high", f"seen in {r.years_seen} years, no reporting surge"
        else:
            conf, why = "medium", "no reporting surge, but limited records or years"
        early = r.first_year == EARLY_YEAR
        where = (f"; already seized in {plural(elsewhere, 'other MENA country').replace('countrys', 'countries')} before"
                 if elsewhere else "; not seen elsewhere in MENA before")
        rows.append(dict(
            signal_type="NEW", country=r.country, drug=r.drug, project_group=r.project_group,
            period=str(r.first_year), records=r.records, change=None, countries=None,
            confidence=conf, confidence_reason=why, is_early=early,
            summary=f"{short(r.drug)} first recorded in {r.country} in {r.first_year} "
                    f"({r.records} records since{', 2025 is incomplete' if early else ''}){where}.",
            rag_query=f"{short(r.drug)} trafficking {r.country} {r.first_year}",
            is_relabel=bool(relabel)))
    return rows


def rising_signals(df, relabels):
    base, recent = df[df["year"].isin(BASE)], df[df["year"].isin(RECENT)]
    b_n, r_n = base.groupby("drug").size(), recent.groupby("drug").size()
    b_share, r_share = b_n / len(base), r_n / len(recent)
    rows = []
    for drug, n in r_n.items():
        if n < RISE_MIN_RECORDS:
            continue
        before = b_share.get(drug, 0)
        change = (r_share[drug] / before - 1) if before else float("inf")
        if change < RISE_MIN_CHANGE:
            continue
        diff = (recent[recent["drug"] == drug].groupby("country").size()
                .sub(base[base["drug"] == drug].groupby("country").size(), fill_value=0))
        up = diff[diff > 0].sort_values(ascending=False)
        top, top_share = up.index[0], up.iloc[0] / up.sum()
        if (top, drug) in relabels and top_share > 0.5:
            conf, why = "low", f"{top} accounts for {top_share:.0%} of the rise and started naming this drug (relabel)"
        elif len(up) >= 2 and top_share <= DOMINANT_SHARE:
            conf, why = "high", f"rise spread across {len(up)} countries"
        elif len(up) >= 2:
            conf, why = "medium", f"{top} accounts for {top_share:.0%} of the rise"
        else:
            conf, why = "low", f"rise comes from {top} only"
        group = df.loc[df["drug"] == drug, "project_group"].iloc[0]
        rows.append(dict(
            signal_type="RISING", country="MENA", drug=drug, project_group=group,
            period="2021-22 to 2023-24", records=int(n), change=change, countries=", ".join(up.index),
            confidence=conf, confidence_reason=why, is_early=False,
            summary=(f"The share of {short(drug)} in MENA seizure records "
                     + (f"rose {change:+.0%}" if before else "went from zero")
                     + f" ({b_n.get(drug, 0)} records in 2021-22, {n} in 2023-24), "
                     f"mostly from {top} ({top_share:.0%} of the increase)."),
            rag_query=f"{short(drug)} increase Middle East North Africa 2023 2024", is_relabel=False))
    return rows


def spreading_signals(df, totals, relabels):
    before = df[df["year"].isin(SPREAD_BASE)].groupby("drug")["country"].apply(set)
    after = df[df["year"].isin(RECENT)].groupby("drug")["country"].apply(set)
    rows = []
    for drug, now in after.items():
        reporting = set(totals[totals.index.get_level_values("year").isin(SPREAD_BASE)]
                        .index.get_level_values("country"))
        new = sorted(c for c in now - before.get(drug, set()) if c in reporting and (c, drug) not in relabels)
        if len(new) < 2:
            continue
        conf = "high" if len(new) >= 3 else "medium"
        group = df.loc[df["drug"] == drug, "project_group"].iloc[0]
        rows.append(dict(
            signal_type="SPREADING", country="MENA", drug=drug, project_group=group,
            period="2019-20 to 2023-24", records=int(df[(df["drug"] == drug) & df["year"].isin(RECENT)].shape[0]),
            change=None, countries=", ".join(new), confidence=conf,
            confidence_reason=f"{len(new)} new countries (all already reporting in 2019-20)", is_early=False,
            summary=f"{short(drug)} seized in {len(new)} more MENA countries in 2023-24 than in 2019-20: {', '.join(new)}.",
            rag_query=f"{short(drug)} spread {' '.join(new[:3])}", is_relabel=False))
    return rows


def main():
    df, totals, all_rows = load()
    new = new_signals(df, totals, all_rows)
    relabels = {(s["country"], s["drug"]) for s in new if s["is_relabel"]}
    signals = pd.DataFrame(new + rising_signals(df, relabels) + spreading_signals(df, totals, relabels))
    order = {"high": 0, "medium": 1, "low": 2}
    signals = signals.sort_values(["signal_type", "confidence", "records"],
                                  key=lambda s: s.map(order) if s.name == "confidence" else s,
                                  ascending=[True, True, False]).reset_index(drop=True)
    signals.insert(0, "signal_id", [f"S{i + 1:02d}" for i in range(len(signals))])
    out = ROOT / "data" / "processed" / "signals"
    out.mkdir(parents=True, exist_ok=True)
    signals.to_csv(out / "mena_signals.csv", index=False, encoding="utf-8")

    def table(kind):
        t = signals[signals["signal_type"] == kind]
        return t[["signal_id", "confidence", "summary", "confidence_reason"]].to_markdown(index=False) if len(t) else "None."

    counts = signals.groupby(["signal_type", "confidence"]).size().unstack(fill_value=0)
    report = f"""# MENA Early-Warning Signals

**Run:** {date.today()} · script `scripts/07_mena_signals.py` · North Africa + Near and Middle East, {df['country'].nunique()} countries
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
{counts.to_markdown()}

## Rising
{table('RISING')}

## Spreading
{table('SPREADING')}

## New in a country
{table('NEW')}

## Limits
- Seizures show what was caught and reported, not how much is used or trafficked.
- Algeria provides over half of MENA records, so regional totals lean towards Algeria.
- Egypt reports few records (about 20-30 a year, none after 2023), so Egypt signals are rare.
"""
    (ROOT / "reports" / "04_mena_signals.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
