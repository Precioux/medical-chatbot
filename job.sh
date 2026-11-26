#!/bin/bash
# Full-PDF extraction with Qwen2-VL-72B (bf16) as runai training jobs on the h200 pool.
# There is no SLURM here, so this replaces sbatch: N jobs × G H200s, each doing every N-th page.
# Usage:   bash job.sh [num-shards=4] [gpus-per-shard=2] [extra extract_pages.py args]
# Logs:    tail -f /mnt/upschrimpf2/scratch/mahdipou/ml/logs/extraction_s*.log   (or runai logs pages-s0 -f)
# Finish:  /mnt/upschrimpf2/scratch/mahdipou/miniconda3/envs/senv/bin/python extract_pages.py --merge
N=${1:-4}
GPUS=${2:-2}
shift $(( $# < 2 ? $# : 2 ))
for ((i=0; i<N; i++)); do
    bash /mnt/upschrimpf2/scratch/mahdipou/config/submit_H.sh h200 pages-s$i \
        "/mnt/mahdipou/ml/extract_pages.py --shard $i --num-shards $N $*" $GPUS 8
done
