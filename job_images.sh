#!/bin/bash
# Part 1: describe the 175 non-decorative Docling pictures with Qwen3-VL-8B on 1x H200 (runai).
# Usage:   bash job_images.sh [extra describe_images.py args, e.g. --limit 5]
# Watch:   runai logs describe-images -f        (per-batch ETA lines)
# Output:  out/image_descriptions.jsonl (+ out/image_descriptions_skipped.jsonl). Resumable: just resubmit.
# Then:    ../miniconda3/envs/senv/bin/python merge_sources.py     (Part 2, CPU, login node)
bash /mnt/upschrimpf2/scratch/mahdipou/config/submit_H.sh h200 describe-images \
    "/mnt/mahdipou/ml/describe_images.py $*" 1 8
