# Medical chatbot: guideline extraction, chunking and translation tests

This repo turns a 474-page Cambodian **Clinical Practice Guidelines for Medicine** PDF (Ministry of Health,
Part 1: Emergency + Cardiology) into verified English chunks for a retrieval (RAG) index. It also tests how well
machine translation handles Khmer, Lao and Vietnamese medical text.

```
source.pdf ──► 1 translate ──► 2 extract ──► 3 verify ──► 4 chunk ──► 5 validate ──► chunks_256.jsonl
 (474 pages)   Khmer → EN      text, tables,   every number    51 sections   checks +      chunks_512.jsonl
               (NLLB)          figures, OCR    and symbol      from the TOC  preview        excluded.jsonl
```

## What the PDF looks like, and where each part of the text comes from

The PDF is a Word export. 469 pages have a real **text layer**, which is the most reliable source; the other pages
are scans. The pipeline combines several sources and records the source of every block in its `source` field:

| Content | Source | Notes |
|---|---|---|
| Body text | PDF text layer (PyMuPDF) | Symbol/Wingdings glyphs decoded (μ ≤ ≥ ↑ ↓ β ×); superscripts written as `10^9` |
| Tables | Docling table grid / mmore markdown, **every cell checked against the text layer** | TIMI score (p287) rebuilt from PyMuPDF `find_tables` |
| Scanned pages (4–8, 165) | Chandra OCR | |
| Flowcharts / algorithms | Chandra OCR | |
| Figures | Qwen3-VL-8B descriptions | not checkable against the PDF → `numbers_verified: false` |
| Khmer text (p1, p266, scanned p4–6) | NLLB-200 1.3B → English, with a quality gate | see *Translation* below |

## The pipeline

One entry point, `run_pipeline.py`. All settings (model paths, chunk sizes, page ranges, thresholds) are in
`config.yaml`. Each stage reads only the previous stage's output (plus the frozen inputs listed under `inputs:` in
the config) and writes to its own folder under `out/pipeline/`.

```bash
python run_pipeline.py                     # all stages; stages already done are skipped
python run_pipeline.py --from chunk        # chunk + validate only
python run_pipeline.py --to translate      # stage 1 only
python run_pipeline.py --force             # rerun even if done
python run_pipeline.py --report            # only rewrite out/pipeline/pipeline_report.md
```

A stage counts as done when its `_done.json` fingerprint matches. The fingerprint covers the stage's code, its
inputs, the previous stage's outputs and its config section, so a stage reruns by itself when any of these change.
`out/pipeline/pipeline_report.md` is rewritten after every run, with the time per stage, translated blocks,
section count, chunk statistics and every validation result.

| # | Stage | Folder | What it does | Stops the pipeline if |
|---|---|---|---|---|
| 1 | `translate` | `stage1_translate/` | Finds non-English text by script (Khmer U+1780–17FF, Lao U+0E80–0EFF, Vietnamese letters) in the text layer, or in Chandra's output on pages without one. Translates it with NLLB-200 1.3B: dash normalisation, sentence split, loop retry, decimal and number-word repair. Scores each translation by back-translating it and comparing with the source (chrF). **Needs a GPU.** | the NLLB worker fails |
| 2 | `extract` | `stage2_extract/` | `build_unified.py`: merges all sources into `unified_output.jsonl` (1,335 blocks) and puts in the translations. A translation is used only if its chrF ≥ `extract.mt_min_chrf` (60); otherwise the block gets an English placeholder that keeps the numbers. The original text stays in metadata. | non-English text is left in a block |
| 3 | `verify` | `stage3_verify/` | `verify_output.py`: compares the output with the PDF text layer page by page: words, numbers, symbols, figures | numbers ≠ 6,362/6,362 or symbols ≠ 245/245 |
| 4 | `chunk` | `stage4_chunk/` | Builds `chunks_256.jsonl` and `chunks_512.jsonl` (BGE-M3 tokens, target 256/512, max 384/768), `excluded.jsonl` and `sections.json` | no sections found in the TOC |
| 5 | `validate` | `stage5_validate/` | Checks both chunk variants (below) and writes `chunks_preview.html` | any check fails |

### Chunking rules (in priority order)

1. Never cross a section boundary. The 51 sections (27 Emergency + 24 Cardiology) come from the PDF's own table
   of contents; each section starts where its title line is found in the text layer.
2. Never split a sentence. Sentences that continue across a line, block or page break are joined first.
3. Tables stay whole; a long table is split by rows, with the header row repeated in each part.
4. Flowcharts stay whole. When Chandra and Qwen3 describe the same figure, the Chandra text is kept and the Qwen3
   text goes into `metadata.alt_description`.
5. Other figure chunks get `numbers_verified: false`.
6. Text chunks overlap by about 15%, in whole sentences. Tables and flowcharts never overlap.
7. Front matter (pages 1–16), chapter title pages and reference lists go to `excluded.jsonl`, not the index.

Chunk schema (one JSON object per line):

```json
{
  "chunk_id": "s10_paracetamol_poisoning_0012",
  "chapter": "I", "section_number": 10, "section_title": "Paracetamol Poisoning",
  "subsection": "VI. DIFFERENTIAL DIAGNOSIS; VII. MANAGEMENT",
  "pages": [122, 123],
  "source_type": "body_text | table | figure | flowchart",
  "text_en": "...", "text_km": null, "text_lo": null, "text_vi": null,
  "embed_text_en": "Chapter I Emergency > 10. Paracetamol Poisoning > VI. ...\n...",
  "citation": "Ch. I §10 Paracetamol Poisoning, pp. 122–123",
  "source": "pdf_text", "block_ids": ["chunk_00313", "..."], "tokens": 241,
  "numbers_verified": true,
  "metadata": {"printed_pages": [109, 110], "overlap_tokens": 0, "...": "..."}
}
```

`pages` are PDF page numbers (printed page = PDF page − 13, also stored in `metadata.printed_pages`).
`numbers_verified` is true only when every number in the chunk is found in the PDF text layer of its pages.

### Validation (stage 5)

| Check | 256 variant | 512 variant |
|---|---|---|
| Numbers / symbols, chunks + excluded, all pages | 6,362/6,362 · 245/245 | 6,362/6,362 · 245/245 |
| Numbers / symbols, index only (p17+, reference lists removed) | 4,430/4,430 · 240/240 | 4,430/4,430 · 240/240 |
| Blocks or sentences missing from chunks and `excluded.jsonl` | 0 | 0 |
| Chunks crossing a section / table parts without header | 0 / 0 | 0 / 0 |
| Citations not matching pages and section | 0 | 0 |
| Chunks | 1,652 | 926 |

Chunks over the maximum length are only flowcharts (kept whole by rule 4) and single table rows that are longer
than the limit.

### Translation (stage 1): a warning

NLLB-1.3B invents whole sentences for short Khmer names and for the PDF text layer's broken Khmer encoding. For
example, a Cambodian snake name on p266 came back as *"How do we know that Jehovah's Witnesses are genuine?"*.
The back-translation chrF gate removes these: 26 of 44 segments are withheld, including all 12 snake-name cells,
whose English names are in the same table row. The original Khmer, the raw MT and its score stay in
`metadata.machine_translation`. Change `extract.mt_min_chrf` / `extract.mt_unreliable` in `config.yaml` to adjust
this; only stage 2 onward reruns, no GPU needed.

## Running it

**Environment.** The conda env `senv` (`../environment.yml`); Python 3.10, PyMuPDF, transformers, sacrebleu, PyYAML.
Models are loaded from the shared Hugging Face cache (`config.yaml: hf_home`, offline). Run as
`../miniconda3/envs/senv/bin/python run_pipeline.py`.

**GPU (stage 1, benchmarks).** On the EPFL RCP cluster, jobs go through runai:

```bash
bash ../config/submit_H.sh h200 pipeline-translate "/mnt/mahdipou/ml/run_pipeline.py --to translate" 1 8
runai logs pipeline-translate -f
```

Stage 1 refuses to run without CUDA (no model code on the login node). Stages 2–5 are CPU-only and take about
1.5 minutes on the login node. NLLB runs in a separate subprocess, because importing transformers after PyMuPDF
fails in the runai container.

**Data that is not in the repo** (see `.gitignore`; it stays on the cluster): `data/source.pdf`, the page renders
`pages/page_NNNN.png`, FLORES-200 (`data/flores200/`), the Khmer medical QA set (`data/khmer-medical-qa/`), the raw
glossary PDFs, Docling's `ocr/output.json`, image crops and the large pipeline outputs (chunk files, previews).
The frozen upstream artifacts the pipeline reads are listed under `inputs:` in `config.yaml`.

## Other experiments in this repo

| Script / notebook | What it tests | Results |
|---|---|---|
| `nllb_full_benchmark.ipynb` | NLLB-200 600M vs 1.3B: FLORES-200 Khmer/Lao/Vietnamese → English, query and document translation for retrieval | `out/nllb_benchmark_results.json` |
| `mt_safety_test.py` | EN → Khmer/Lao/Vietnamese with NLLB-1.3B on 50 guideline chunks: numbers, negations, drug names, units, back-translation (`--variant fixed` adds the pre/post-processing the pipeline uses) | `out/mt_safety/REPORT.md` |
| `build_glossary.py`, `glossary_mt.py`, `ocr_glossary.py`, `tess_glossary.py` | OCR of the MOH English–Lao medical glossary; NLLB with glossary terms and drug names protected by placeholders | `out/glossary_mt/`, `out/mt_safety/` |
| `translation_agent.py` | NLLB-1.3B vs small LLMs as translation agents (Llama-2-7B, Llama-3.1-8B, Gemma-3-4B, Qwen3-VL-8B text-only): BLEU, chrF++, COMET, numbers kept, loops, speed | `out/translation_agent_report.md`, `out/translation_agent_results.json`, `out/translation_agent_bleu.png` |
| `crosslingual_*.ipynb` | Cross-lingual retrieval with BGE-M3 and other embedders, Khmer medical questions vs English answers | `out/xling_*` |
| `fill_gaps.py`, `extract_pages.py`, `describe_images.py`, `merge_sources.py` | Earlier extraction steps: VLM gap filling, page/table extraction, Qwen3-VL figure descriptions, the mmore-based merge | `out/` |

`CLAUDE.md` has the detailed working notes: model decisions, known issues and cluster tips.

## Repository layout

```
run_pipeline.py        entry point            config.yaml       all settings
pipeline/              stage code: translate.py, extract.py, verify.py, chunk.py, validate.py, report.py, common.py
build_unified.py       stage 2 builder        verify_output.py  stage 3 checker (shared with stage 5)
merge_sources.py       TOC, Chandra/mmore helpers used by build_unified
out/pipeline/          stage outputs + pipeline_report.md (large files not in git)
out/                   other results and reports
```
