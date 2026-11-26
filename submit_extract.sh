#!/bin/bash
# Launch N parallel Qwen2-VL-72B table-extraction shards on runai H200 nodes.
# Usage: bash submit_extract.sh [num-shards=4] [gpus-per-shard=2] [extra args for extract_tables.py]
# bf16 72B is ~146 GB of weights -> 2 x H200 (141 GB each) per shard.
# When all shards finish: python merge_tables.py
N=${1:-4}
GPUS=${2:-2}
shift $(( $# < 2 ? $# : 2 ))
EXTRA="$*"
for ((i=0; i<N; i++)); do
    bash /mnt/upschrimpf2/scratch/mahdipou/config/submit_H.sh h200 tables-s$i \
        "/mnt/mahdipou/ml/extract_tables.py --shard $i --num-shards $N $EXTRA" $GPUS 8
done
echo "Watch: runai logs tables-s0 -f   |   all: runai list jobs"
