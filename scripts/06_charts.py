"""Static charts (PNG) telling the 'plants to labs' story. Reads the analysis CSVs.

Colours: validated reference palette, fixed slot order (blue, orange, aqua, yellow) for the
four drug groups; muted gray for the misleading 'simple total' line. Complete years only
(2011-2024); 2025-2026 are incomplete and left out.
Output: reports/charts/*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "analysis"
OUT = ROOT / "reports" / "charts"
YEARS = range(2011, 2025)
SOURCE = "Source: UNODC Drugs Monitoring Platform, Individual Drug Seizures (IDS). Analysis: own calculations."

SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GROUP_COLORS = {"Plant-based": BLUE, "Synthetic": ORANGE, "Pharmaceutical": AQUA,
                "New psychoactive substances": YELLOW}
LAB = "Lab-made (synthetic + NPS)"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "text.color": INK,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "lines.linewidth": 2, "savefig.dpi": 200, "axes.axisbelow": True,
})


def frame(fig, title, subtitle):
    fig.text(0.04, 0.95, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.885, subtitle, fontsize=11.5, color=INK_2, va="top")
    fig.text(0.04, 0.025, SOURCE, fontsize=8.5, color=MUTED)


def pct_axis(ax, top=None):
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0, top)
    ax.tick_params(length=0)
    ax.set_xlim(min(YEARS) - 0.3, max(YEARS) + 0.3)


def end_label(ax, x, y, text, color):
    ax.plot([x], [y], "o", ms=8, color=color, mec=SURFACE, mew=2, zorder=5)
    ax.annotate(text, (x, y), xytext=(10, 0), textcoords="offset points", va="center",
                fontsize=10.5, color=INK, fontweight="bold")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, facecolor=SURFACE)
    plt.close(fig)
    print("saved", OUT / name)


def world():
    w = pd.read_csv(ANALYSIS / "world_mix_by_method.csv")
    return w[w["year"].isin(YEARS)]


def chart_method_matters(w):
    lab = w[(w["project_group"] == LAB) & (w["measure"] == "records")]
    series = [("pooled", "Simple total (all rows added up)", MUTED),
              ("country_avg", "Every country counts equally", BLUE),
              ("significant_only", "Significant seizures only (UNODC rule)", ORANGE)]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.subplots_adjust(left=0.07, right=0.80, top=0.80, bottom=0.12)
    for method, label, color in series:
        s = lab[lab["method"] == method].set_index("year")["share"]
        ax.plot(s.index, s.values, color=color, label=label)
        end_label(ax, s.index[-1], s.iloc[-1], f"{s.iloc[-1]:.0%}", color)
    pct_axis(ax, 0.35)
    ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=INK_2)
    col = lab[(lab["method"] == "pooled") & (lab["year"] == 2016)]["share"].iloc[0]
    ax.annotate("Colombia's 200k+ small street\nseizures pull the total down",
                (2016, col), xytext=(2016.3, 0.13), fontsize=9.5, color=INK_2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    frame(fig, "Lab-made drugs rose from ~15% to ~25% of seizures, once every country counts fairly",
          "Share of seizure records that are synthetic drugs or new psychoactive substances, 2011–2024")
    save(fig, "01_method_matters.png")


def chart_records_vs_weight(w):
    lab = w[(w["project_group"] == LAB) & (w["method"] == "significant_only")]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.subplots_adjust(left=0.07, right=0.84, top=0.80, bottom=0.12)
    for measure, label, color in [("records", "By number of records", BLUE), ("weight", "By weight (kg)", ORANGE)]:
        s = lab[lab["measure"] == measure].set_index("year")["share"]
        ax.plot(s.index, s.values, color=color, label=label)
        end_label(ax, s.index[-1], s.iloc[-1], f"{s.iloc[-1]:.0%}", color)
    pct_axis(ax, 0.35)
    ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=INK_2)
    frame(fig, "Lab-made drugs are seized often, but in small amounts",
          "Lab-made share of seizures by records vs by weight · significant seizures only, every country counts equally")
    save(fig, "02_records_vs_weight.png")


def chart_group_mix(w):
    m = w[(w["measure"] == "records") & (w["method"] == "significant_only")
          & (w["project_group"].isin(GROUP_COLORS))]
    t = m.pivot(index="year", columns="project_group", values="share")[list(GROUP_COLORS)]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.subplots_adjust(left=0.07, right=0.78, top=0.78, bottom=0.12)
    ax.stackplot(t.index, t.T.values, colors=list(GROUP_COLORS.values()),
                 edgecolor=SURFACE, linewidth=1.5, labels=list(GROUP_COLORS))
    pct_axis(ax, 1.0)
    ax.grid(False)
    cum = t.cumsum(axis=1)
    last = t.index[-1]
    for g in GROUP_COLORS:
        mid = cum.loc[last, g] - t.loc[last, g] / 2
        ax.annotate(f"{g}  {t.loc[last, g]:.0%}", (last, mid), xytext=(12, 0), textcoords="offset points",
                    va="center", fontsize=10, color=INK)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.04, 0.845), ncol=4,
               frameon=False, fontsize=9.5, labelcolor=INK_2)
    frame(fig, "Plant-based drugs still dominate, but their share is shrinking",
          "Mix of seizure records by drug group · significant seizures only, every country counts equally")
    save(fig, "03_drug_group_mix.png")


def chart_regions():
    r = pd.read_csv(ANALYSIS / "region_mix.csv")
    r = r[(r["project_group"] == LAB) & (r["measure"] == "records") & (r["method"] == "country_avg")
          & (r["year"].isin(YEARS))]
    regions = ["Asia", "Europe", "Oceania", "Africa", "Americas"]

    # countries behind each point: same rule as the country average (>= 20 drug records that year)
    df = pd.read_parquet(ROOT / "data" / "processed" / "ids_clean.parquet",
                         columns=["year", "region", "country", "project_group"])
    df = df[df["year"].isin(YEARS) & df["project_group"].isin(GROUP_COLORS)]
    per_country = df.groupby(["region", "year", "country"]).size()
    countries = per_country[per_country >= 20].groupby(level=["region", "year"]).size()

    fig, axes = plt.subplots(2, 5, figsize=(14, 6.6), sharey="row", sharex=True,
                             gridspec_kw={"height_ratios": [3, 1], "hspace": 0.12})
    fig.subplots_adjust(left=0.06, right=0.98, top=0.76, bottom=0.15, wspace=0.12)
    for col, region in enumerate(regions):
        ax, axc = axes[0, col], axes[1, col]
        s = r[r["region"] == region].set_index("year")["share"].sort_index()
        avg = s.rolling(3, min_periods=2).mean()
        ax.plot(s.index, s.values, color=MUTED, lw=1, label="Single year")
        ax.plot(avg.index, avg.values, color=BLUE, label="3-year average")
        end_label(ax, avg.index[-1], avg.iloc[-1], f"{avg.iloc[-1]:.0%}", BLUE)
        pct_axis(ax, 0.7)
        ax.set_title(region, loc="left", fontsize=12, fontweight="bold", color=INK)

        c = countries.loc[region].reindex(YEARS, fill_value=0)
        axc.bar(c.index, c.values, color=MUTED, width=0.7, edgecolor=SURFACE, linewidth=1)
        axc.annotate(f"{c.iloc[-1]}", (c.index[-1], c.iloc[-1]), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=9, color=INK_2)
        axc.tick_params(length=0)
        axc.set_xlim(2010.5, 2026.5)
        axc.set_xticks([2012, 2018, 2024])
    axes[1, 0].set_ylabel("Countries", fontsize=9.5, color=INK_2)
    axes[0, 0].legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK_2)
    frame(fig, "Asia leads the shift to lab-made drugs; the Americas and Africa stay plant-based",
          "Lab-made share of seizure records by region (every country counts equally) · bars: reporting countries per year")
    fig.text(0.04, 0.065, "Fewer reporting countries = less reliable. Oceania = 1 reporting country, no 2024 data. "
             "3-year average smooths jumps when countries join or leave.", fontsize=9, color=INK_2)
    save(fig, "04_regions.png")


def chart_mena():
    d = pd.read_csv(ANALYSIS / "mena_top_drugs.csv")
    lookup = pd.read_csv(ROOT / "data" / "reference" / "drug_class_lookup.csv")[["drug", "project_group"]]
    d = d[d["year"].between(2020, 2024)].merge(lookup, on="drug", how="left")
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.76, bottom=0.12, wspace=0.75)
    for ax, sub in zip(axes, ["Near and Middle East", "North Africa"]):
        t = (d[d["subregion"] == sub].groupby(["drug", "project_group"])["records"].sum()
             .reset_index().nlargest(7, "records").iloc[::-1])
        names = t["drug"].str.replace(r" \(.*\)", "", regex=True)
        ax.barh(names, t["records"], color=t["project_group"].map(GROUP_COLORS).fillna(MUTED),
                height=0.62, edgecolor=SURFACE, linewidth=2)
        for y, v in enumerate(t["records"]):
            ax.annotate(f"{v:,}", (v, y), xytext=(5, 0), textcoords="offset points", va="center",
                        fontsize=9.5, color=INK_2)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID)
        ax.tick_params(length=0, labelsize=10)
        ax.tick_params(axis="y", colors=INK)
        ax.set_title(sub, loc="left", fontsize=12, fontweight="bold", color=INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in GROUP_COLORS.values()]
    fig.legend(handles, list(GROUP_COLORS), loc="upper left", bbox_to_anchor=(0.04, 0.84), ncol=4,
               frameon=False, fontsize=9.5, labelcolor=INK_2)
    frame(fig, "Captagon leads in the Middle East; pregabalin is #2 in North Africa",
          "Most-seized drugs by number of records, 2020–2024")
    save(fig, "05_mena_top_drugs.png")


def chart_colombia():
    df = pd.read_parquet(ROOT / "data" / "processed" / "ids_clean.parquet", columns=["year", "country"])
    s = df[df["year"].isin(YEARS)].groupby("year")["country"].apply(lambda c: (c == "Colombia").mean())
    fig, ax = plt.subplots(figsize=(11, 6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.78, bottom=0.12)
    ax.bar(s.index, s.values, color=BLUE, width=0.7, edgecolor=SURFACE, linewidth=2)
    peak = s.idxmax()
    ax.annotate(f"{s[peak]:.0%}", (peak, s[peak]), xytext=(0, 5), textcoords="offset points",
                ha="center", fontsize=10.5, fontweight="bold", color=INK)
    ax.annotate(f"{s.iloc[-1]:.0%}", (s.index[-1], s.iloc[-1]), xytext=(0, 5), textcoords="offset points",
                ha="center", fontsize=10.5, fontweight="bold", color=INK)
    pct_axis(ax, 1.0)
    frame(fig, "One country can dominate the data: Colombia was most of all records in 2014–2016",
          "Colombia's share of all seizure records per year · why this project weights every country equally")
    save(fig, "06_colombia_share.png")


def main():
    w = world()
    chart_method_matters(w)
    chart_records_vs_weight(w)
    chart_group_mix(w)
    chart_regions()
    chart_mena()
    chart_colombia()


if __name__ == "__main__":
    main()
