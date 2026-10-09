"""Can the report library explain the MENA signals? A keyword check run before building RAG.

For each signal, search the extracted report pages (data/docs/pages.jsonl) for the drug and
the place (the country, or MENA terms for region-wide signals):
  strong  a page mentions both the drug and the place
  weak    pages mention the drug, but none together with the place
  none    the drug is not mentioned at all
  close   stricter: drug and place within 300 characters (about one paragraph) on the same page
A keyword match shows the library has relevant text; it does not prove the text explains the signal.

Input:  data/docs/pages.jsonl, data/docs/sources.csv, data/processed/signals/mena_signals.csv
Output: data/docs/signal_coverage.csv, reports/05_doc_coverage.md
"""
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DRUG_TERMS = {
    "Alprazolam (Xanax, Pranax, Ksalol)": ["alprazolam"],
    "Benzodiazepines": ["benzodiazepine"],
    "Cannabis herb (marijuana)": ["cannabis herb", "marijuana", "cannabis"],
    "Clonazepam (Rivotril)": ["clonazepam"],
    "Cocaine base": ["cocaine"],
    "Cocaine hydrochloride (HCl, powder cocaine)": ["cocaine"],
    "Non-specified cocaine-type": ["cocaine"],
    "Diazepam": ["diazepam"],
    "Fenethylline": ["fenetylline", "fenethylline", "captagon"],
    "Heroin": ["heroin"],
    "JWH - 018": ["jwh-018", "synthetic cannabinoid"],
    "MDMA": ["mdma", "ecstasy"],
    "Non-specified ecstasy-type substances": ["ecstasy", "mdma"],
    "Methamphetamine": ["methamphetamine"],
    "Non-specified hallucinogens": ["hallucinogen"],
    "Non-specified synthetic cannabinoids (spice)": ["synthetic cannabinoid"],
    "Other synthetic cannabinoids (spice)": ["synthetic cannabinoid"],
    "Pregabalin": ["pregabalin"],
    "Subutex (buprenorphine)": ["buprenorphine"],
    "Tramadol": ["tramadol"],
}
PLACE_TERMS = {
    "Syrian Arab Republic": ["syrian arab republic", "syria"],
    "United Arab Emirates": ["united arab emirates"],
    "State of Palestine": ["state of palestine", "palestine"],
    "MENA": ["middle east", "north africa", "west asia", "western asia", "arab countries", "arab region"],
}


def has_any(text: str, terms: list[str]) -> bool:
    return any(re.search(r"\b" + re.escape(t), text) for t in terms)


def near(text: str, terms_a: list[str], terms_b: list[str], window: int = 300) -> bool:
    a = [m.start() for t in terms_a for m in re.finditer(r"\b" + re.escape(t), text)]
    b = [m.start() for t in terms_b for m in re.finditer(r"\b" + re.escape(t), text)]
    return any(abs(i - j) <= window for i in a for j in b)


def main() -> None:
    pages = [json.loads(line) for line in open(ROOT / "data" / "docs" / "pages.jsonl", encoding="utf-8")]
    for p in pages:
        p["low"] = p["text"].lower()
    titles = pd.read_csv(ROOT / "data" / "docs" / "sources.csv").set_index("doc_id")["title"]
    signals = pd.read_csv(ROOT / "data" / "processed" / "signals" / "mena_signals.csv")

    rows = []
    for s in signals.itertuples():
        drug_terms = DRUG_TERMS[s.drug]
        places = PLACE_TERMS.get(s.country, [s.country.lower()])
        if s.country == "MENA" and isinstance(s.countries, str):      # region-wide: also the listed countries
            places = places + [PLACE_TERMS.get(c, [c.lower()])[0] for c in s.countries.split(", ")]
        drug_pages = [p for p in pages if has_any(p["low"], drug_terms)]
        both = [p for p in drug_pages if has_any(p["low"], places)]
        close = [p for p in both if near(p["low"], drug_terms, places)]
        level = "strong" if both else ("weak" if drug_pages else "none")
        best = both or drug_pages
        docs = pd.Series([p["doc_id"] for p in best]).value_counts()
        example = best[0] if best else None
        rows.append({
            "signal_id": s.signal_id, "signal_type": s.signal_type, "confidence": s.confidence,
            "country": s.country, "drug": s.drug, "coverage": level,
            "pages_drug": len(drug_pages), "pages_drug_and_place": len(both), "pages_close": len(close),
            "top_docs": ", ".join(docs.index[:3]),
            "example": f"{example['doc_id']} p.{example['page_label']}" if example else "",
            "close_example": f"{close[0]['doc_id']} p.{close[0]['page_label']}" if close else "",
        })
    cov = pd.DataFrame(rows)
    cov.to_csv(ROOT / "data" / "docs" / "signal_coverage.csv", index=False)

    by_conf = (cov.groupby(["confidence", "coverage"]).size().unstack(fill_value=0)
               .reindex(["high", "medium", "low"]).reindex(columns=["strong", "weak", "none"], fill_value=0))
    doc_use = (cov[cov["coverage"] == "strong"]["top_docs"].str.split(", ").explode().value_counts()
               .rename_axis("doc_id").reset_index(name="signals_with_strong_match"))
    doc_use["title"] = doc_use["doc_id"].map(titles)
    gaps = cov[cov["pages_close"] == 0][["signal_id", "confidence", "country", "drug", "coverage"]]
    close_by_conf = cov.groupby("confidence")["pages_close"].apply(lambda x: f"{(x > 0).sum()} of {len(x)}")

    report = f"""# Report library coverage of MENA signals

**Run:** {date.today()} · script `scripts/10_doc_coverage.py` · {len(pages):,} report pages, {len(titles) - 1} reports used
**Method:** keyword search. *Strong* = a page names both the drug and the country (or MENA for region-wide
signals); *weak* = the drug is mentioned but never with that place; *none* = drug not mentioned.
A match means relevant text exists; it does not prove the text explains the signal.

## Coverage by signal confidence
{by_conf.to_markdown()}

**Total:** {(cov.coverage == 'strong').sum()} of {len(cov)} signals strong, {(cov.coverage == 'weak').sum()} weak, {(cov.coverage == 'none').sum()} none.

## Stricter check: drug and place in the same paragraph (within 300 characters)
**{(cov.pages_close > 0).sum()} of {len(cov)} signals** have such a passage. By confidence:
high {close_by_conf.get('high', '-')}, medium {close_by_conf.get('medium', '-')}, low {close_by_conf.get('low', '-')}.
This is the better guide to what the assistant can explain with a direct citation.

## Most useful reports (signals with a strong match)
{doc_use.to_markdown(index=False)}

## Signals without a same-paragraph match (gaps)
{gaps.to_markdown(index=False) if len(gaps) else 'None.'}

Full table: `data/docs/signal_coverage.csv`.
"""
    (ROOT / "reports" / "05_doc_coverage.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
