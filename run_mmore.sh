#!/bin/bash
# Runs inside a runai GPU job: mmore process on data/source.pdf.
# Raw output: out/mmore/run/merged/merged_results.jsonl
# Copies (no post-processing): out/mmore/mmore_output.json (the sample record) and
# out/mmore/mmore_output.md (its "text" field, verbatim).
set -ex
cd /mnt/mahdipou/ml
export HF_HOME=/mnt/mahdipou/hf_cache
export PYTHONPATH=/mnt/mahdipou/envs/mmore PYTHONNOUSERSITE=1
PY=/mnt/mahdipou/miniconda3/envs/senv/bin/python3.10
nvidia-smi --query-gpu=index,name,memory.total --format=csv
time $PY -s -m mmore process --config-file out/mmore/process_config.yaml
$PY -s - <<'PYEOF'
import json
recs = [json.loads(l) for l in open("out/mmore/run/merged/merged_results.jsonl") if l.strip()]
assert len(recs) == 1, f"expected 1 sample, got {len(recs)}"
r = recs[0]
json.dump(r, open("out/mmore/mmore_output.json", "w"), ensure_ascii=False, indent=2)
open("out/mmore/mmore_output.md", "w").write(r["text"])
print("DONE:", len(r["text"]), "chars,", len(r.get("modalities", [])), "modalities")
PYEOF
