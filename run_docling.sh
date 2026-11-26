#!/bin/bash
# Runs inside a runai GPU job: converts data/source.pdf -> output.json with Docling.
# The file is written to a temp dir and moved into place in one step, because the
# Qwen extraction jobs start as soon as output.json exists.
set -ex
cd /mnt/mahdipou/ml
export HF_HOME=/mnt/mahdipou/hf_cache
TMP=docling_tmp
mkdir -p $TMP
nvidia-smi --query-gpu=index,name,memory.total --format=csv
export PYTHONPATH=/mnt/mahdipou/envs/docling/lib/python3.10/site-packages PYTHONNOUSERSITE=1
time /mnt/mahdipou/miniconda3/envs/senv/bin/python -s -m docling.cli.main data/source.pdf --to json --output $TMP \
    --device cuda --num-threads 16 -v
mv $TMP/source.json output.json.part && mv output.json.part output.json
echo "DONE: $(/mnt/mahdipou/miniconda3/envs/senv/bin/python -c "import json;print(len(json.load(open(\"output.json\"))[\"tables\"]))") tables"
