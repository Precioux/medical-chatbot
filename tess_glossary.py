"""Tesseract (tessdata_best; TESS_LANGS env, default lao+eng) OCR of the rendered Lao glossary pages, for comparison with Chandra.
    python tess_glossary.py [page ...]     -> out/glossary_ocr/tess_pNNN.txt
Uses the separate conda env ../miniconda3/envs/ocrenv (tesseract 5.5) so senv is untouched."""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
TESS = os.path.join(ROOT, "..", "miniconda3", "envs", "ocrenv", "bin", "tesseract")
TESSDATA = os.path.join(ROOT, "..", "models", "tessdata")
PNG = os.path.join(ROOT, "out", "glossary_ocr", "lao_png")
LANGS = os.environ.get("TESS_LANGS", "lao+eng")
pages = [int(p) for p in sys.argv[1:]] or sorted(int(f[1:4]) for f in os.listdir(PNG))
for p in pages:
    out = os.path.join(ROOT, "out", "glossary_ocr", f"tess_{LANGS.replace('+', '-')}_p{p:03d}")
    subprocess.run([TESS, os.path.join(PNG, f"p{p:03d}.png"), out, "--tessdata-dir", TESSDATA,
                    "-l", LANGS, "--psm", "3"], check=True)
    print("done", p, flush=True)
