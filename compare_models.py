#!/usr/bin/env python
"""Score the page-43 NEWS-2 table from Docling, mmore and Chandra (dots.ocr dropped).

    python compare_models.py            # -> out/model_comparison.json + a table on stdout

Six ground-truth cells (given by the user). Columns on the page: 3 2 1 0 1 2 3, so
"Score 3" is the first value column (left) and "Score 1" (left) is the third.
Docling and mmore have no page markers in their markdown, so their NEWS-2 table is
found by its "Respiratory rate (/ minute)" row. For mmore, paragraph_starts is used
to confirm which page that table is on (its ids run 1..474). Chandra uses page 43 from
its per-page JSONL. Both markdown pipe tables and HTML tables (colspan expanded)
are parsed.
"""
import bisect
import html
import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
PAGE = 43

# (row key, column index among value columns, expected, label for the report)
TRUTH = [
    ("respiratory rate", 0, "≤8", "Respiratory rate, Score 3"),
    ("spo2 scale 1", 0, "≤91", "SpO2 scale 1, Score 3"),
    ("systolic", 0, "≤90", "Systolic BP, Score 3"),
    ("temperature", 0, "≤35.0", "Temperature, Score 3"),
    ("respiratory rate", 2, "9-11", "Respiratory rate, Score 1"),
    ("pulse", 0, "≤40", "Pulse, Score 3 (left)"),
]
ROW_KEYS = sorted({k for k, *_ in TRUTH})


def clean_cell(s):
    s = html.unescape(s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("**", "").replace("$", "").strip()


def norm(s):
    s = (s or "").replace("<=", "≤").replace(">=", "≥").replace("\\leq", "≤").replace("\\le", "≤")
    s = s.replace("\\geq", "≥").replace("\\ge", "≥").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", "", s).lower()


class _Tables(HTMLParser):
    """Collect HTML tables as lists of rows; colspan cells are repeated."""
    def __init__(self):
        super().__init__()
        self.tables, self.row, self.cell, self.span = [], None, None, 1

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell, self.span = "", int(dict(attrs).get("colspan", 1) or 1)
        elif tag == "br" and self.cell is not None:
            self.cell += " "

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row += [self.cell.strip()] * self.span
            self.cell = None
        elif tag == "tr" and self.row is not None and self.tables:
            self.tables[-1].append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data


def table_rows(text):
    """All table rows in text (markdown pipe rows and HTML rows) as lists of cells."""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", s):
            rows.append([clean_cell(c) for c in s.strip("|").split("|")])
    p = _Tables()
    p.feed(text)
    for t in p.tables:
        rows += [[clean_cell(c) for c in r] for r in t]
    return rows


def news_rows(text):
    """Map row key -> value cells (label column dropped). First match per key wins."""
    found = {}
    for r in table_rows(text):
        if not r:
            continue
        label = norm(r[0])
        for k in ROW_KEYS:
            if norm(k) in label and k not in found:
                found[k] = r[1:]
    return found


def score(text):
    rows = news_rows(text)
    checks = []
    for key, col, want, name in TRUTH:
        cells = rows.get(key)
        got = cells[col] if cells is not None and col < len(cells) else None
        checks.append({"check": name, "expected": want, "got": got,
                       "ok": got is not None and norm(got) == norm(want)})
    return checks, sorted(rows)


def snippet_around(text, anchor="respiratory rate (/ minute)", before=2500, after=4000):
    i = text.lower().find(anchor)
    return (None, None) if i < 0 else (text[max(0, i - before):i + after], i)


def load_sources():
    src = {}
    docling = open(os.path.join(ROOT, "ocr", "output.md")).read()
    src["Docling"] = dict(text=snippet_around(docling)[0], where="ocr/output.md (NEWS-2 table found by row label)")

    mm = json.load(open(os.path.join(OUT, "mmore", "mmore_output.json")))
    text, pos = snippet_around(mm["text"])
    where = "out/mmore/mmore_output.md (NEWS-2 table found by row label)"
    ps = mm["metadata"].get("paragraph_starts") or []
    if pos is not None and ps:
        offs = [p[0] for p in ps]
        page_id = ps[max(0, bisect.bisect_right(offs, pos) - 1)][1]
        where += f"; paragraph_starts puts it on page {page_id}"
    src["mmore"] = dict(text=text, where=where)

    for name, model in (("Chandra", "chandra"),):  # dots.ocr dropped 2026-11-22
        fn = os.path.join(OUT, f"{model}_pages.jsonl")
        rec = None
        if os.path.exists(fn):
            rec = next((json.loads(l) for l in open(fn) if json.loads(l)["page"] == PAGE), None)
        src[name] = dict(text=rec["content"] if rec else None, where=f"out/{model}_pages.jsonl page {PAGE}",
                         rec=rec)
    return src


def notes_for(name, s, checks, rows_found):
    if s["text"] is None:
        return "no output for page 43 (run not finished?)"
    if not rows_found:
        return "NEWS-2 table not found / not parseable as a table"
    bad = [f"{c['check']}: got {c['got']!r}" for c in checks if not c["ok"]]
    parts = [f"rows found {len(rows_found)}/{len(ROW_KEYS)}"]
    rec = s.get("rec") or {}
    if rec.get("hit_max"):
        parts.append("hit max_new_tokens")
    if rec.get("json_ok") is False:
        parts.append("layout JSON not parseable, raw text scored")
    parts.append("wrong: " + "; ".join(bad) if bad else "all 6 correct")
    return ", ".join(parts)


def main():
    results = []
    for name, s in load_sources().items():
        checks, rows_found = score(s["text"]) if s["text"] else ([], [])
        n_ok = sum(c["ok"] for c in checks)
        results.append({"model": name, "key_values_correct": n_ok, "key_values_total": len(TRUTH),
                        "notes": notes_for(name, s, checks, rows_found), "source": s["where"],
                        "rows_found": rows_found, "checks": checks})
    out = {"page": PAGE, "table": "NATIONAL EARLY WARNING SCORE 2 (NEWS-2)",
           "ground_truth": [{"check": n, "expected": w} for _, _, w, n in TRUTH],
           "normalization": "whitespace removed, <=/>= -> ≤/≥, en/em dash -> '-', lowercase",
           "results": results}
    fn = os.path.join(OUT, "model_comparison.json")
    json.dump(out, open(fn, "w"), ensure_ascii=False, indent=2)

    print("| Model | Key values (out of 6) | Page 43 notes |\n|---|---|---|")
    for r in results:
        print(f"| {r['model']} | {r['key_values_correct']}/6 | {r['notes']} |")
    print(f"\nSaved {fn}")


if __name__ == "__main__":
    main()
