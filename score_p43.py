#!/usr/bin/env python
"""Score page 43 (NEWS-2) extractions against hand-checked values.

Usage: python score_p43.py out/tables_shard*.jsonl out/q3vl8b_shard0.jsonl ...
Checks the 4 reference values given by the user (all in the first score column, "3")
plus the full grid read off the page image, so column shifts are caught too.
"""
import json
import re
import sys

# Column order on the page: 3 2 1 0 1 2 3. "" = empty cell.
TRUTH = {
    "respiratory rate": ["≤8", "", "9-11", "12-20", "", "21-24", "≥75"],
    "spo2 scale 1":     ["≤91", "92-93", "94-95", "≥96", "", "", ""],
    "spo2 scale 2":     ["≤83", "84-85", "86-87", "88-92 ≥93 on air", "93-94 on oxygen",
                         "95-96 on oxygen", "≥97 on oxygen"],
    "air or oxygen":    ["", "Oxygen", "", "Air", "", "", ""],
    "systolic":         ["≤90", "91-100", "101-110", "111-219", "", "", "≥220"],
    "pulse":            ["≤40", "", "41-50", "51-90", "91-110", "111-130", "≥131"],
    "consciousness":    ["", "", "", "Alert", "", "", "CVPU"],
    "temperature":      ["≤35.0", "", "35.1-36.0", "36.1-38.0", "38.1-39.0", "≥39.1", ""],
}
KEY_CHECKS = [("respiratory rate", "≤8"), ("spo2 scale 1", "≤91"),
              ("systolic", "≤90"), ("temperature", "≤35.0")]


def norm(s):
    s = s.replace("<=", "≤").replace(">=", "≥").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", "", s).lower()
    return "" if s in {"-", "", "n/a"} else s


def parse_rows(md):
    rows = {}
    for line in md.splitlines():
        if not line.strip().startswith("|") or re.match(r"^\s*\|[\s|:-]+\|\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        label = cells[0].lower()
        for key in TRUTH:
            if key in label and key not in rows:
                rows[key] = cells[1:]
    return rows


def score(md):
    rows = parse_rows(md)
    key = []
    for k, want in KEY_CHECKS:
        got = rows.get(k, [None])[0] if rows.get(k) else None
        key.append((k, want, got, got is not None and norm(got) == norm(want)))
    n_ok = n_all = 0
    for k, truth in TRUTH.items():
        got = rows.get(k, [])
        for j, t in enumerate(truth):
            n_all += 1
            n_ok += j < len(got) and norm(got[j]) == norm(t)
    return key, n_ok, n_all, rows


def main():
    for fn in sys.argv[1:]:
        for line in open(fn):
            r = json.loads(line)
            if r["page"] != 43:
                continue
            name = r.get("model", fn).rstrip("/").split("/")[-1] + f" [{r.get('mode', 'page')}]"
            key, n_ok, n_all, rows = score(r["content"])
            print(f"\n=== {name}  ({fn})")
            for k, want, got, ok in key:
                print(f"  {'OK ' if ok else 'BAD'} {k:17s} score 3: want {want:7s} got {got!r}")
            print(f"  key values: {sum(x[3] for x in key)}/4   full grid: {n_ok}/{n_all} cells "
                  f"({100 * n_ok / n_all:.0f}%)   rows found: {len(rows)}/8")


if __name__ == "__main__":
    main()
