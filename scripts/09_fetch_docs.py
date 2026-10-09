"""Download the report library for the RAG assistant and extract text page by page.

Input:  data/docs/sources.csv (one row per report; URLs verified by hand)
Output: data/docs/pdf/<doc_id>.pdf      local copies only, never published
        data/docs/pages.jsonl            one line per page: doc_id, page (position in the PDF, 1-based),
                                         page_label (number printed on the page), text
        data/docs/docs_status.csv        download and extraction result per report

Reports whose site blocks scripts (host_note starts with 'manual') are used only if the PDF has been
saved by hand as data/docs/pdf/<doc_id>.pdf. Existing PDFs are not downloaded again.
"""
import json
import re
from pathlib import Path

import pandas as pd
import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data" / "docs"
PDF_DIR = DOCS / "pdf"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def download(url: str, path: Path) -> str:
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError("response is not a PDF")
    path.write_bytes(r.content)
    return f"downloaded ({len(r.content) / 1e6:.1f} MB)"


def clean(text: str) -> str:
    text = re.sub(r"-\n(?=[a-z])", "", text)        # re-join words split across lines
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    sources = pd.read_csv(DOCS / "sources.csv")
    status, pages = [], []
    for src in sources.itertuples():
        path = PDF_DIR / f"{src.doc_id}.pdf"
        row = {"doc_id": src.doc_id, "status": "", "pages": 0, "empty_pages": 0}
        try:
            if path.exists():
                row["status"] = "already saved"
            elif str(src.host_note).startswith("manual"):
                row["status"] = "skipped: save by hand from the URL to use it"
                status.append(row)
                continue
            else:
                row["status"] = download(src.url, path)
            reader = PdfReader(path)
            for i, page in enumerate(reader.pages):
                text = clean(page.extract_text() or "")
                label = reader.page_labels[i] if i < len(reader.page_labels) else str(i + 1)
                if len(text) < 30:
                    row["empty_pages"] += 1
                    continue
                pages.append({"doc_id": src.doc_id, "page": i + 1, "page_label": label, "text": text})
            row["pages"] = len(reader.pages)
        except Exception as e:                      # keep going; the failure is reported
            row["status"] = f"FAILED: {type(e).__name__}: {e}"[:200]
        status.append(row)
        print(f"{src.doc_id:28s} {row['status']:28s} pages={row['pages']:4d} empty={row['empty_pages']}")

    with open(DOCS / "pages.jsonl", "w", encoding="utf-8") as f:
        for p in pages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    pd.DataFrame(status).to_csv(DOCS / "docs_status.csv", index=False)
    print(f"\n{len(pages):,} pages with text from {sum(s['pages'] > 0 for s in status)} reports -> {DOCS / 'pages.jsonl'}")


if __name__ == "__main__":
    main()
