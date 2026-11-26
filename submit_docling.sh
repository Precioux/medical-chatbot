#!/bin/bash
# Docling conversion as a runai training job on one H200 (writes ml/output.json).
runai delete job docling 2>/dev/null
runai submit --name docling -i preciouxch/precioux --gpu 1 --cpu 16 --large-shm \
    --node-pools h200 --pvc "upschrimpf2-scratch:/mnt/" \
    --command -- bash /mnt/mahdipou/ml/run_docling.sh
echo "Watch: runai logs docling -f"
