#!/bin/bash
# mmore process as a runai job on one H200 (writes out/mmore/).
# Uses an Ubuntu 22.04 image (not preciouxch/precioux): torch>=2.7 (needed by surya) needs glibc>=2.28.
runai delete job mmore 2>/dev/null
runai submit --name mmore -i nvidia/cuda:12.8.1-base-ubuntu22.04 --gpu 1 --cpu 16 --large-shm \
    --run-as-uid 316718 --run-as-gid 30393 --supplemental-groups 80443 \
    --node-pools h200 --pvc "upschrimpf2-scratch:/mnt/" \
    --command -- bash /mnt/mahdipou/ml/run_mmore.sh
echo "Watch: runai logs mmore -f"
