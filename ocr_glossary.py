#!/usr/bin/env python
"""OCR the scanned MOH English-Lao Medical Glossary (data/glossaries/raw/lao/B01577.pdf) with Chandra.

    python ocr_glossary.py --pages 30,60,100      # quick quality test on a few pages
    python ocr_glossary.py                        # all pages (resumable)

Output: out/glossary_ocr/lao_pages.jsonl  {"page": N, "content": "..."}  (0-based PDF page index)
Page images are rendered at 200 DPI into out/glossary_ocr/lao_png/.
"""
import argparse, json, os

from ocr_models import load, generate
from extract_pages import log

ROOT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(ROOT, "data", "glossaries", "raw", "lao", "B01577.pdf")
OUT = os.path.join(ROOT, "out", "glossary_ocr")
PNG = os.path.join(OUT, "lao_png")
JSONL = os.path.join(OUT, "lao_pages.jsonl")

PROMPT = ("This page is from a bilingual English-Lao medical glossary (with French and Thai equivalents). "
          "Transcribe every entry exactly as printed, in reading order (left column, then right column). "
          "Keep the Lao script (ພາສາລາວ) and Thai script exactly; do not translate or romanise anything. "
          "Output plain text, one line per printed line.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="")
    ap.add_argument("--max-new-tokens", type=int, default=3000)
    a = ap.parse_args()
    model, processor = load("chandra")   # load before importing pymupdf (first attempt died in torch imports)
    import pymupdf
    os.makedirs(PNG, exist_ok=True)
    doc = pymupdf.open(PDF)
    pages = [int(p) for p in a.pages.split(",")] if a.pages else list(range(doc.page_count))
    done = {json.loads(l)["page"] for l in open(JSONL)} if os.path.exists(JSONL) else set()
    pages = [p for p in pages if p not in done]
    for p in pages:
        path = os.path.join(PNG, f"p{p:03d}.png")
        if not os.path.exists(path):
            doc[p].get_pixmap(dpi=200).save(path)
        texts, n_tok = generate(model, processor, PROMPT, [path], a.max_new_tokens)
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps({"page": p, "content": texts[0], "n_tok": n_tok[0]}, ensure_ascii=False) + "\n")
        log(f"page {p}: {n_tok[0]} tokens")


if __name__ == "__main__":
    main()
