#!/usr/bin/env python
"""Merge out/tables_shard*.jsonl into tables_extracted.jsonl, sorted by (table_index, page)."""
import glob, json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
recs, seen = [], set()
for fn in sorted(glob.glob(os.path.join(ROOT, "out/tables_shard*.jsonl"))):
    for line in open(fn):
        r = json.loads(line)
        key = (r["table_index"], r["page"])
        if key not in seen:
            seen.add(key); recs.append(r)
recs.sort(key=lambda r: (r["table_index"], r["page"]))
with open(os.path.join(ROOT, "tables_extracted.jsonl"), "w") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
n_tab = len({r["table_index"] for r in recs})
empty = sum(1 for r in recs if not r["markdown"])
mism = sorted({r["page"] for r in recs if r["n_tables_model"] != r["n_tables_docling"]})
print(f"{len(recs)} records, {n_tab} distinct tables, {empty} with empty markdown")
print(f"pages where model/Docling table counts differ ({len(mism)}): {mism}")
