"""Drug Seizures Explorer: interactive view of the UNODC Individual Drug Seizures data.

Run:  streamlit run app/app.py
Data: app/data/ids_summary.parquet (built by scripts/08_build_app_data.py)
"""
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"
SOURCE = "Source: UNODC Drugs Monitoring Platform, Individual Drug Seizures (IDS)."
GROUP_COLORS = {"Plant-based": "#2a78d6", "Synthetic": "#eb6834", "Pharmaceutical": "#1baf7a",
                "New psychoactive substances": "#eda100", "Precursors & chemicals": "#898781",
                "Other / unspecified": "#c3c2b7"}
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INCOMPLETE = {2025, 2026}
PLOT_CONFIG = {"displaylogo": False, "displayModeBar": True, "scrollZoom": False,
               "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}

st.set_page_config(page_title="Drug Seizures Explorer", layout="wide")


# ---------- data ----------
CHANGE_LABELS = {"NEW": "New in a country", "RISING": "Growing", "SPREADING": "Spreading to more countries"}


@st.cache_data
def load():
    df = pd.read_parquet(DATA / "ids_summary.parquet")
    for c in df.select_dtypes("category"):
        df[c] = df[c].astype(str)
    signals = pd.read_csv(DATA / "mena_signals.csv")
    signals["signal_type"] = signals["signal_type"].map(CHANGE_LABELS)
    covid = pd.read_csv(DATA / "covid_monthly.csv", parse_dates=["date"])
    panel = pd.read_csv(DATA / "covid_panel_countries.csv")["country"].tolist()
    return df, signals, covid, panel


@st.cache_data
def to_excel(df: pd.DataFrame, sheet: str) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xl:
        df.to_excel(xl, sheet_name=sheet[:31], index=False)
        ws = xl.sheets[sheet[:31]]
        for i, col in enumerate(df.columns):
            ws.set_column(i, i, min(max(len(str(col)), df[col].astype(str).str.len().max()) + 2, 60))
        ws.write(len(df) + 2, 0, SOURCE)
    return buf.getvalue()


def download(df: pd.DataFrame, name: str, key: str):
    st.download_button("Download table (Excel)", to_excel(df, name), file_name=f"{name}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=key)


def show_chart(fig, name: str, key: str, legend_below: bool = False):
    fig.update_layout(font=dict(family="Segoe UI, system-ui, sans-serif", size=13, color="#0b0b0b"),
                      title=dict(font=dict(size=16), x=0, xanchor="left"),
                      margin=dict(l=20, r=20, t=90, b=40), plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb",
                      legend=dict(title_text="", orientation="h", x=0, xanchor="left",
                                  **({"yanchor": "top", "y": -0.12} if legend_below else {"yanchor": "bottom", "y": 1.02})))
    fig.update_xaxes(showgrid=False, automargin=True, tickfont=dict(color="#52514e"), title_font=dict(color="#52514e"))
    fig.update_yaxes(gridcolor="#e1e0d9", automargin=True, tickfont=dict(color="#52514e"),
                     title_font=dict(color="#52514e"))
    config = {**PLOT_CONFIG, "toImageButtonOptions": {**PLOT_CONFIG["toImageButtonOptions"], "filename": name}}
    st.plotly_chart(fig, use_container_width=True, config=config, key=key, theme=None)


def fmt(n: float) -> str:
    return f"{n:,.0f}"


df, signals, covid, covid_panel = load()

# ---------- sidebar filters ----------
st.sidebar.title("Filters")
measure_label = st.sidebar.radio("Measure", ["Number of records", "Weight (kg)"],
                                 help="Records = how many seizures. Weight = how much was seized "
                                      "(only seizures reported in grams or kg).")
significant = st.sidebar.checkbox("Only significant seizures (UNODC rule)",
                                  help="Cannabis and opium 1 kg or more; other drugs 100 g or more; "
                                       "new psychoactive substances any amount. Makes countries comparable.")
if significant:
    MEASURE = "significant_records" if measure_label == "Number of records" else "significant_kg"
else:
    MEASURE = "records" if measure_label == "Number of records" else "weight_kg"
UNIT = "records" if measure_label == "Number of records" else "kg"

years = st.sidebar.slider("Years", 2011, 2026, (2011, 2024))
if INCOMPLETE & set(range(years[0], years[1] + 1)):
    st.sidebar.caption("2025 and 2026 are incomplete: many countries have not reported yet.")

regions = st.sidebar.multiselect("Region", sorted(df["region"].unique()))
pool = df[df["region"].isin(regions)] if regions else df
subregions = st.sidebar.multiselect("Subregion", sorted(pool["subregion"].unique()))
pool = pool[pool["subregion"].isin(subregions)] if subregions else pool
countries = st.sidebar.multiselect("Country", sorted(pool["country"].unique()))

groups = st.sidebar.multiselect("Drug group", list(GROUP_COLORS))
dpool = df[df["project_group"].isin(groups)] if groups else df
drugs = st.sidebar.multiselect("Drug name", sorted(dpool["drug"].unique()))

f = df[df["year"].between(*years)]
for col, chosen in [("region", regions), ("subregion", subregions), ("country", countries),
                    ("project_group", groups), ("drug", drugs)]:
    if chosen:
        f = f[f[col].isin(chosen)]
fy = df[df["year"].between(*years)]              # f without geography filters, for comparisons
for col, chosen in [("project_group", groups), ("drug", drugs)]:
    if chosen:
        fy = fy[fy[col].isin(chosen)]
st.sidebar.caption(SOURCE)

# ---------- header ----------
st.title("Drug Seizures Explorer")
st.caption(f"{SOURCE} Seizures show what was caught and reported, not how much drug is used or trafficked.")
if f.empty:
    st.warning("No data for these filters. Try widening the years or removing a filter.")
    st.stop()

tabs = st.tabs(["Overview", "Country profile", "Drug profile", "COVID-19", "MENA early warning",
                "Data & downloads", "FAQ"])


# ---------- shared chart builders ----------
def kpis(data, one_country=False, one_drug=False):
    c = st.columns(4)
    c[0].metric("Seizure records", fmt(data["significant_records" if significant else "records"].sum()))
    kg = data["significant_kg" if significant else "weight_kg"].sum()
    c[1].metric("Weight seized (kg)", f"{kg / 1e6:.1f} million" if kg >= 1e6 else fmt(kg))
    if one_country:          # a single country: show how many years it reported instead
        c[2].metric("Years with data", data["year"].nunique())
    else:
        c[2].metric("Countries", data["country"].nunique())
    if one_drug:             # a single drug: show how many years it was seized instead
        c[3].metric("Years with data", data["year"].nunique())
    else:
        c[3].metric("Drug types", data["drug"].nunique())


def trend_chart(data, key, title):
    as_share = st.radio("Show as", ["Totals", "% of each year"], horizontal=True, key=f"{key}_share",
                        help="'% of each year' shows the mix of drug groups, which is fairer when "
                             "the number of reporting countries changes.")
    t = data.groupby(["year", "project_group"])[MEASURE].sum().reset_index()
    if as_share == "% of each year":
        t[MEASURE] = t[MEASURE] / t.groupby("year")[MEASURE].transform("sum") * 100
    fig = px.bar(t, x="year", y=MEASURE, color="project_group", color_discrete_map=GROUP_COLORS,
                 category_orders={"project_group": list(GROUP_COLORS)}, title=title,
                 labels={MEASURE: "% of year" if as_share != "Totals" else UNIT, "year": "",
                         "project_group": "Drug group"})
    fig.update_traces(marker_line_color="#fcfcfb", marker_line_width=1,
                      hovertemplate="%{x}<br>%{fullData.name}: %{y:,.0f}<extra></extra>")
    fig.update_xaxes(tickmode="linear", dtick=1, tickformat="d", tickangle=0)
    fig.update_layout(height=430, bargap=0.25)
    show_chart(fig, key, key)
    pivot = t.pivot(index="year", columns="project_group", values=MEASURE).fillna(0).round(1).reset_index()
    return pivot


def top_bar(data, by, n, key, title):
    t = (data.groupby([by, "project_group"])[MEASURE].sum().reset_index()
         .sort_values(MEASURE, ascending=False).head(n))
    plot = t.assign(label=t[by].str.replace(r" \(.*\)", "", regex=True))    # "Cannabis resin (hashish)" -> "Cannabis resin"
    fig = px.bar(plot, x=MEASURE, y="label", orientation="h", color="project_group",
                 color_discrete_map=GROUP_COLORS, category_orders={"project_group": list(GROUP_COLORS)},
                 title=title, labels={MEASURE: "", "label": "", "project_group": "Drug group"},   # unit is in the title
                 hover_data={by: True, "label": False})
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False,
                      marker_line_color="#fcfcfb", marker_line_width=1)
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_xaxes(range=[0, plot[MEASURE].max() * 1.15])
    fig.update_layout(height=max(380, 30 * len(t) + 200), bargap=0.3)
    show_chart(fig, key, key, legend_below=True)
    return t


def world_map(data, key, title):
    t = data.groupby(["iso3", "country"])[MEASURE].sum().reset_index()
    fig = px.choropleth(t, locations="iso3", color=MEASURE, hover_name="country",
                        color_continuous_scale=BLUES, title=title, labels={MEASURE: UNIT})
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="equal earth",
                    showcountries=True, countrycolor="#e1e0d9", showland=True, landcolor="#f0efec")
    if t["iso3"].nunique() < 40:          # a region or a few countries chosen: zoom to them
        fig.update_geos(fitbounds="locations")
    fig.update_layout(height=430, dragmode="pan")
    show_chart(fig, key, key)
    st.caption("Map: use the + / − buttons (top right) to zoom, drag to move, "
               "and the home button to reset. Scrolling moves the page, not the map.")
    return t.sort_values(MEASURE, ascending=False)


# ---------- Overview ----------
with tabs[0]:
    kpis(f)
    st.caption("Tip: hover a chart and click the camera icon to save it as a PNG image.")
    trend = trend_chart(f, "trend_by_group", f"Seizures by drug group per year ({UNIT})")
    download(trend, "trend_by_group", "dl_trend")
    left, right = st.columns(2)
    with left:
        top = top_bar(f, "drug", 10, "top_drugs", f"Top 10 drugs ({UNIT})")
        download(top, "top_drugs", "dl_top_drugs")
    with right:
        top_c = top_bar(f, "country", 10, "top_countries", f"Top 10 countries ({UNIT})")
        download(top_c, "top_countries", "dl_top_countries")
    st.caption("Large totals often reflect how much a country reports, not only how much it seizes.")
    m = world_map(f, "world_map", f"Seizures by country ({UNIT})")
    download(m, "by_country", "dl_map")

# ---------- Country profile helpers ----------
DRUG_GROUPS = list(GROUP_COLORS)[:4]
LAB = ["Synthetic", "New psychoactive substances"]


def group_shares(data):
    t = data[data["project_group"].isin(DRUG_GROUPS)].groupby("project_group")["records"].sum()
    return (t / t.sum() * 100).reindex(DRUG_GROUPS, fill_value=0)


def region_average(context, subregion, exclude):
    """Average drug-group mix of the other countries in the subregion (each country counts equally)."""
    others = context[(context["subregion"] == subregion) & (context["country"] != exclude)]
    sizes = others.groupby("country")["records"].sum()
    others = others[others["country"].isin(sizes[sizes >= 20].index)]
    if others["country"].nunique() == 0:
        return None, 0
    shares = pd.DataFrame({k: group_shares(g) for k, g in others.groupby("country")}).T
    return shares.mean(), len(shares)


def country_summary(c, country):
    years = sorted(c["year"].unique())
    total = c["records"].sum()
    top = c.groupby("drug")["records"].sum().sort_values(ascending=False)
    lab = c[c["project_group"].isin(LAB)]
    lab_share = lab["records"].sum() / total * 100 if total else 0
    text = (f"**{country}** reported **{total:,} seizures** in **{len(years)} years** ({years[0]}-{years[-1]}). "
            f"The most-seized drug is **{top.index[0]}** ({top.iloc[0]:,} records, {top.iloc[0] / total:.0%}). "
            f"Lab-made drugs (synthetic and new psychoactive substances) are **{lab_share:.0f}%** of records")
    if len(lab):
        first = lab["year"].min()
        if first > years[0]:
            first_drug = lab[lab["year"] == first].groupby("drug")["records"].sum().idxmax()
            text += f"; they first appear in **{first}** ({first_drug})"
    return text + "."


def country_notes(c, country, context, subregion):
    notes = []
    total = c["records"].sum()
    per_year = c.groupby("year")["records"].sum()
    if per_year.mean() < 50:
        notes.append(f"**Little data:** about {per_year.mean():.0f} records a year, so year-to-year changes "
                     "may not be reliable.")
    missing = [y for y in range(per_year.index.min(), per_year.index.max() + 1) if y not in per_year.index]
    if missing:
        notes.append(f"**Gaps in reporting:** no data for {', '.join(map(str, missing))}.")
    for i, (y, n) in enumerate(per_year.items()):       # first sharp rise vs the years before it
        before = per_year.iloc[:i]
        if len(before) >= 2 and n > 3 * before.median() and n >= 100:
            notes.append(f"**Reporting grew sharply in {y}:** {n:,} records vs about {before.median():,.0f} "
                         "a year before, likely because the country started reporting more seizures.")
            break
    if total >= 100:
        small = 1 - c["significant_records"].sum() / total
        if small >= 0.7:
            notes.append(f"**Reports many small seizures:** {small:.0%} of its records are below UNODC's "
                         "'significant' size (street level). Its totals look large partly for this reason.")
        elif small <= 0.2:
            notes.append(f"**Reports mainly large seizures:** only {small:.0%} of its records are small, "
                         "so street-level activity is not visible in its data.")
    world_year = context.groupby("year")["records"].sum()
    dom = (per_year / world_year.reindex(per_year.index)).dropna()
    if len(dom) and dom.max() >= 0.3:
        notes.append(f"**Dominates the data:** in {dom.idxmax()}, {country} was {dom.max():.0%} of all records "
                     "worldwide, so world totals that year mostly reflect this country.")
    vague = c[c["drug"].str.startswith(("Non-specified", "Other"))]["records"].sum() / total if total else 0
    if vague >= 0.3:
        notes.append(f"**General drug names:** {vague:.0%} of records use general categories "
                     "(for example 'Non-specified ...'), so the exact drug is often unknown.")
    avg, _ = region_average(context, subregion, country)
    if avg is not None and total >= 20:
        own = group_shares(c)
        for g in DRUG_GROUPS:
            if abs(own[g] - avg[g]) >= 20:
                word = "more" if own[g] > avg[g] else "less"
                notes.append(f"**Different from its region:** {g.lower()} drugs are {own[g]:.0f}% of its records, "
                             f"{word} than the average in the rest of {subregion} ({avg[g]:.0f}%).")
        region_top = (context[(context["subregion"] == subregion) & (context["country"] != country)]
                      .groupby("drug")["records"].sum().nlargest(5).index)
        top_drug = c.groupby("drug")["records"].sum().idxmax()
        if len(region_top) and top_drug not in region_top:
            notes.append(f"**Unusual top drug:** its most-seized drug, {top_drug}, is not among the top 5 "
                         f"in the rest of {subregion}.")
    return notes


# ---------- Country profile ----------
with tabs[1]:
    options = sorted(f["country"].unique())
    default = options.index("Egypt") if "Egypt" in options else 0
    country = st.selectbox("Choose a country", options, index=default)
    c = f[f["country"] == country]
    subregion = c["subregion"].iloc[0]
    kpis(c, one_country=True)
    st.markdown(country_summary(c, country))
    st.caption(f"Years with data: {', '.join(map(str, sorted(c['year'].unique())))} · "
               f"Region: {c['region'].iloc[0]} / {subregion}")

    notes = country_notes(c, country, fy, subregion)
    if notes:
        st.markdown("#### What stands out")
        for note in notes:
            st.markdown(f"- {note}")

    ct = trend_chart(c, f"{country}_trend", f"{country}: seizures by drug group per year")
    download(ct, f"{country}_trend", "dl_c_trend")

    left, right = st.columns(2)
    with left:
        top_bar(c, "drug", 15, f"{country}_drugs", f"{country}: most-seized drugs ({UNIT})")
    with right:
        avg, n_countries = region_average(fy, subregion, country)
        if avg is not None:
            comp = pd.DataFrame({"Drug group": DRUG_GROUPS, country: group_shares(c).values,
                                 f"Rest of {subregion} (average)": avg.values})
            long = comp.melt(id_vars="Drug group", var_name="Who", value_name="% of records")
            long["Drug group"] = long["Drug group"].replace({"New psychoactive substances": "New psychoactive<br>substances"})
            fig = px.bar(long, x="Drug group", y="% of records", color="Who", barmode="group",
                         color_discrete_sequence=["#2a78d6", "#898781"], text="% of records",
                         title=f"{country} vs the rest of {subregion} (% of records)")
            fig.update_traces(texttemplate="%{y:.0f}%", textposition="outside", cliponaxis=False,
                              hovertemplate="%{fullData.name}<br>%{x}: %{y:.1f}%<extra></extra>")
            fig.update_yaxes(range=[0, 110], ticksuffix="%", title="")
            fig.update_xaxes(title="")
            fig.update_layout(height=460, bargap=0.3, bargroupgap=0.08)
            show_chart(fig, f"{country}_vs_region", "c_vs_region")
            st.caption(f"Average of {n_countries} other countries in {subregion}, each counted equally.")
            download(comp.round(1), f"{country}_vs_region", "dl_c_region")
        else:
            st.info(f"No other country in {subregion} has enough data for a comparison.")

    st.markdown(f"#### {country}: all drugs, records and weight")
    table = (c.groupby(["drug", "project_group"])
             .agg(records=("records", "sum"), weight_kg=("weight_kg", "sum"),
                  years=("year", "nunique")).reset_index()
             .sort_values("records", ascending=False))
    table["% of records"] = (table["records"] / table["records"].sum() * 100).round(1)
    table["weight_kg"] = table["weight_kg"].round(1)
    st.dataframe(table, use_container_width=True, hide_index=True)
    download(table, f"{country}_drugs", "dl_c_drugs")

    cs = signals[signals["country"] == country]
    if len(cs):
        st.markdown(f"#### Early-warning signals for {country}")
        st.dataframe(cs[["signal_type", "confidence", "summary", "confidence_reason"]],
                     use_container_width=True, hide_index=True)

# ---------- Drug profile ----------
with tabs[2]:
    drug_counts = f.groupby("drug")["records"].sum().sort_values(ascending=False)   # most common first
    drug = st.selectbox("Choose a drug (most common first)", drug_counts.index.tolist(),
                        format_func=lambda name: f"{name}  ·  {drug_counts[name]:,} records",
                        help="Sorted by number of records for the current filters. Type to search.")
    d = f[f["drug"] == drug]
    kpis(d, one_drug=True)
    st.caption(f"Drug group: {d['project_group'].iloc[0]} · UNODC class: {d['unodc_class'].iloc[0]}")
    t = d.groupby("year")[MEASURE].sum().reset_index()
    fig = px.line(t, x="year", y=MEASURE, markers=True, title=f"{drug}: seizures per year",
                  labels={MEASURE: UNIT, "year": ""}, color_discrete_sequence=[GROUP_COLORS[d["project_group"].iloc[0]]])
    show_chart(fig, f"{drug}_trend", "drug_trend")
    left, right = st.columns(2)
    with left:
        dc = top_bar(d, "country", 10, f"{drug}_countries", f"{drug}: top countries ({UNIT})")
        download(dc, f"{drug}_countries", "dl_d_countries")
    with right:
        dm = world_map(d, f"{drug}_map", f"{drug}: where it is seized")
        download(dm, f"{drug}_by_country", "dl_d_map")

# ---------- COVID-19 ----------
with tabs[3]:
    st.subheader("Did COVID-19 affect drug seizures?")
    st.markdown("**Yes.** In April 2020, during the first lockdowns, seizures fell to about "
                "**one third of normal**. They recovered by autumn 2020 and were above normal in 2021.\n\n"
                "Not every drug group fell: **plant-based** drugs dropped the most (30% of normal), while "
                "**new psychoactive substances** did not drop at all (117%), possibly because they are often "
                "bought online and sent by post. Use the menu below to compare groups.")
    group = st.selectbox("Drug group", ["All drugs"] + list(GROUP_COLORS)[:4], key="covid_group")
    cv = covid[covid["group"] == group].sort_values("date")
    fig = px.line(cv, x="date", y="index", markers=True,
                  title=f"Seizure records per month, {group.lower()} (100 = normal level)",
                  labels={"index": "% of normal", "date": ""},
                  color_discrete_sequence=[GROUP_COLORS.get(group, "#2a78d6")],
                  hover_data={"records": ":,", "index": ":.0f"})
    fig.add_vrect(x0="2020-03-01", x1="2020-06-01", fillcolor="#898781", opacity=0.15, line_width=0,
                  annotation_text="First lockdowns", annotation_position="top left")
    fig.add_hline(y=100, line_color="#898781", line_width=1)
    show_chart(fig, f"covid_{group}", "covid_chart")
    download(cv[["date", "group", "records", "baseline_2018_19", "index"]].assign(date=cv["date"].dt.strftime("%Y-%m")),
             f"covid_monthly_{group}", "dl_covid")
    st.caption(f"Based on the same {len(covid_panel)} countries in every year (each reported at least 100 "
               "seizures a year in 2018-2021), so changes in reporting cannot explain the dip. "
               "'Normal' = the 2018-2019 average for the same month. Sidebar filters do not apply here.")
    with st.expander("Which countries are included?"):
        st.write(", ".join(covid_panel))
    st.info("Fewer seizures does not mean fewer drugs. Borders closed, travel stopped and police were "
            "busy enforcing lockdowns, so fewer drugs were caught and recorded.")

# ---------- MENA early warning ----------
with tabs[4]:
    st.subheader("Early-warning signals: Middle East and North Africa")
    st.markdown("Signals point to drugs that are **new in a country**, **growing**, or **spreading to more "
                "countries**. **Confidence** shows how likely the signal is real rather than "
                "a change in how a country reports (for example, starting to name a drug it used to "
                "record under a general category).")
    a, b = st.columns(2)
    kinds = a.multiselect("Signal type", list(CHANGE_LABELS.values()), default=list(CHANGE_LABELS.values()))
    confs = b.multiselect("Confidence", ["high", "medium", "low"], default=["high", "medium"])
    s = signals[signals["signal_type"].isin(kinds) & signals["confidence"].isin(confs)]
    st.dataframe(s[["signal_id", "signal_type", "confidence", "summary", "confidence_reason"]],
                 use_container_width=True, hide_index=True)
    download(s, "mena_signals", "dl_signals")
    st.caption("2025 is incomplete. Low-confidence signals are hidden by default; add 'low' to see them.")

# ---------- Data & downloads ----------
with tabs[5]:
    st.subheader("Filtered data")
    st.caption("One row per year, country and drug. Individual seizure records are not shared, "
               "following UNODC's data-use guidance.")
    view = f.drop(columns=["is_incomplete_year"]).sort_values(["year", "country", "drug"])
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption(f"{len(view):,} rows")
    download(view, "drug_seizures_filtered", "dl_all")

# ---------- FAQ ----------
FAQ = [
    ("What is this data?",
     "Drug seizures reported by governments to the UN Office on Drugs and Crime (UNODC), 2011 to mid-2026. "
     "Each record is one seizure: where, when, which drug and how much."),
    ("Does more seizures mean more drugs in a country?",
     "Not necessarily. Seizures depend on police activity and on how much a country reports. "
     "A country with many records may simply report every small seizure."),
    ("What is the difference between 'records' and 'weight'?",
     "Records = how many seizures. Weight = how many kilograms. Cannabis is seized in large amounts, "
     "so it dominates weight; pills like ecstasy or captagon are small, so they show more in records."),
    ("What does 'significant seizures only' do?",
     "It keeps only seizures above UNODC's size rules (cannabis 1 kg or more, most other drugs 100 g or more). "
     "Some countries report every small seizure and others only big ones; this option makes them comparable."),
    ("Why are 2025 and 2026 marked incomplete?",
     "Countries report with a delay. Only about half the usual countries have reported for 2025 so far, "
     "and 2026 covers January to June only."),
    ("Why does Egypt have so little data?",
     "Egypt reported only about 20 to 30 seizures a year, in 6 of the years. That is enough to see which drugs "
     "appear, but not to measure reliable trends."),
    ("What are the drug groups?",
     "Plant-based: cannabis, cocaine, heroin, opium, khat. Synthetic: made in labs, such as methamphetamine, "
     "ecstasy and captagon. Pharmaceutical: medicines misused, such as tramadol and pregabalin. "
     "New psychoactive substances: newer lab drugs that imitate others, such as synthetic cannabinoids ('spice')."),
    ("What is captagon?",
     "A stimulant pill trafficked mainly in the Middle East. Originally the brand name of a medicine "
     "(fenethylline), today it usually contains amphetamine."),
    ("Did COVID-19 affect drug seizures?",
     "Yes. In April 2020 seizures fell to about a third of normal, then recovered by autumn 2020. "
     "This shows that borders and police activity changed, not necessarily that fewer drugs were around. "
     "See the COVID-19 tab."),
    ("What does an early-warning signal mean?",
     "A drug that is new in a country, growing, or spreading to more countries. It is a prompt to look closer, "
     "not proof of a trend. Check the confidence level and the reason given."),
    ("How do I save a chart or a table?",
     "Charts: hover over the chart and click the camera icon to save a PNG. Tables: use the "
     "'Download table (Excel)' button under each chart or on the 'Data & downloads' tab."),
    ("Can I use these numbers in my own work?",
     "Yes, if you cite the source: 'UNODC Drugs Monitoring Platform'. The data may contain some duplicates "
     "and does not include every seizure in the world."),
]
with tabs[6]:
    st.subheader("Frequently asked questions")
    for q, a in FAQ:
        with st.expander(q):
            st.write(a)
