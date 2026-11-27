# ml

Extracting a scanned Cambodian clinical-practice-guideline PDF to markdown.

## Pipeline (Part 1): `run_pipeline.py` + `config.yaml`
One entry point, settings in `config.yaml` (model paths, chunk sizes, page ranges, thresholds). Python:
`../miniconda3/envs/senv/bin/python`. Stages live in `pipeline/` and write to `out/pipeline/<stage folder>/`.
Each stage reads only the previous stage's output (plus the frozen upstream artifacts listed under `inputs:` in the
config). A stage is skipped when its `_done.json` fingerprint (its code, inputs, previous-stage outputs and config
section) is unchanged. `--force` reruns the selected stages, and a stage whose inputs changed reruns automatically.
`out/pipeline/pipeline_report.md` is rewritten after every call (`--report` rewrites only the report).

| # | stage | folder | what | where |
|---|---|---|---|---|
| 1 | `translate` | `stage1_translate/` | Khmer/Lao (Unicode block) and Vietnamese (letters, >=3 words/line) text -> English with NLLB-200 1.3B (fixed mt_safety pipeline + number-word repair + back-translation chrF as a quality estimate). Text layer; Chandra on pages with no text layer. Found: p1, p266 (text layer), p4-6 (Chandra) | **GPU**: `bash ../config/submit_H.sh h200 pipeline-translate "/mnt/mahdipou/ml/run_pipeline.py --to translate" 1 8` |
| 2 | `extract` | `stage2_extract/` | `build_unified.main()` + stage-1 translations (source `nllb-1.3b`, `metadata.original_text/original_language/machine_translation`). A translation is used only if `extract.mt_min_chrf` (60) is reached; otherwise an English placeholder that keeps the numbers | login node |
| 3 | `verify` | `stage3_verify/` | `verify_output.main()`; **stops** unless numbers 6362/6362 and symbols 245/245; copies `unified_output.verified.jsonl` for stage 4 | login node |
| 4 | `chunk` | `stage4_chunk/` | `chunks_256.jsonl`, `chunks_512.jsonl` (BGE-M3 tokens; target 256/max 384, 512/768), `excluded.jsonl` (front matter p1-16, chapter title page, reference lists), `sections.json` (TOC parse: 51 sections, 27 + 24) | login node |
| 5 | `validate` | `stage5_validate/` | `validation.json`, `chunks_preview.html`; **stops** on any failed check | login node |

Run: `python run_pipeline.py` (all; stage 1 is skipped if it is done, otherwise it refuses to run without CUDA and prints the
runai command), `--from chunk`, `--to translate`, `--force`.
- In the runai container, importing transformers after pymupdf fails (`torch._dynamo` ImportError
  `NP_SUPPORTED_MODULES`; senv holds mixed torch 2.6/2.8 files). Stage 1 therefore runs NLLB in a subprocess
  (`python -m pipeline.translate <job.json>`) that never imports pymupdf.
- NLLB invents whole sentences for short Khmer names and for the broken Khmer encoding of the text layer (p266:
  "How do we know that Jehovah's Witnesses ..."). That is why the chrF gate exists. All 12 p266 cells are withheld;
  their English names are in the same table row.
- Chunking rules are in the `pipeline/chunk.py` docstring. Sections are cut where each TOC title line is found in the
  text layer, never at Docling headings. Over-max chunks are only flowcharts (kept whole) and single table rows.
- Stage 4 also (2026-11-27): cites the **printed** page (PDF page - 13, checked against every page footer; `pages` keep
  the PDF page); applies page-image-checked OCR fixes (`chunk.text_fixes`) and LaTeX -> text before chunking (stage 5
  applies the same `fix_text`); joins stray `##` lines (`stray_headings.json`); renames repeated-number score headers
  (NEWS-2; `metadata.original_header`); merges chunks < 40 tokens into the next chunk of the same section
  (`metadata.merged_from`); tags document errata from `chunk.errata` (`out/pipeline/errata.json`, `metadata.errata`,
  text unchanged); writes `out/pipeline/manual_review_tables.csv` (tables with numbers_verified=false).
  Document typo: PDF p284's footer says 288 (it is printed page 271; the page is a chapter title page, not indexed).
- `verify_output.coverage()` is shared by stages 3 and 5. `norm_text` maps Khmer/Lao digits to ASCII.

## Layout
- `data/source.pdf`: source document (474 pages, ~31 MB). It is a Word 2019 export with a **real text layer** on 469 pages (English; Khmer only on p1 and p266. Scanned p4-6 are Khmer too: Chandra's Khmer OCR of them is hallucinated, repeating lines; the English versions are p7-8). Pages 4-8 and figures/flowcharts are images and need OCR/VLM. (Earlier notes saying there is no text layer were wrong; found 2026-11-25.)
- `pages/page_NNNN.png`: cached 200-DPI renders of every page
- `ocr/output.md`: Docling OCR of the whole PDF (no page markers). This is the main text.
- `pages_extracted.jsonl` / `output.md`: per-page extraction by qwen2-vl-72b (older run). Now only used as a page index by `fill_gaps.py`.
- `extract_pages.py`: per-page / table-page VLM extraction (shards, resumable). Shared helpers (`load_model`, `render_page`, `log`).
- `fill_gaps.py`: fills what Docling left out of `ocr/output.md` with Qwen3-VL-8B (see below)
- `mt_safety_test.py`: EN->KH/LO/VI NLLB-1.3B medical safety test (numbers/negation/drugs/units/back-translation) on 50 guideline chunks; results in `out/mt_safety/REPORT.md`. `--variant fixed` adds the needed pre/post-processing.
- `ocr_glossary.py` (Chandra) / `tess_glossary.py` (Tesseract, separate conda env `../miniconda3/envs/ocrenv`, models in `../models/tessdata`): OCR of the MOH English-Lao Medical Glossary (`data/glossaries/raw/lao/B01577.pdf`) -> `out/glossary_ocr/`
- `build_glossary.py --lao|--merge`: parse Lao OCR (Tesseract primary, Chandra cross-check) + Wikidata vi labels -> `data/medical_glossary.json` (all `reviewed: false`; `use` flags = auto-apply policy for the test only)
- `glossary_mt.py --translate [--protect-only]`: NLLB with `TERM1` placeholders (glossary terms / drug names + abbreviations kept verbatim) -> `out/mt_safety/translations_{glossary,protect}.jsonl`
- `describe_images.py` (+ `job_images.sh`, runai): crops the 175 Docling pictures >= 5000 pt^2 from `pages/` and describes them with Qwen3-VL-8B -> `out/images/`, `out/image_descriptions.jsonl` (DECORATIVE/small -> `out/image_descriptions_skipped.jsonl`). Resumable.
- `merge_sources.py` (CPU): mmore text + Chandra algorithms (de-duplicated against mmore) + Docling table grids + Qwen3 image descriptions -> `out/unified_output.jsonl` (chapter/section from the printed TOC, PDF page = printed + 13) and `out/merge_report.json`
- `build_unified.py` (CPU, senv python): builder of `out/unified_output.jsonl` (standalone) and stage 2 of the pipeline (`main(out, report_path, translations)`). Text from the PDF text layer (Symbol/Wingdings private-use glyphs decoded: μ ≤ ≥ ↑ ↓ β ×), tables = Docling grid / mmore table with every cell checked against the text layer, TIMI (p287) rebuilt from PyMuPDF find_tables, Chandra for pages with no text layer (4-8, 165), algorithms (Chandra) and image descriptions (Qwen3) unchanged. `source` field says where each block came from. The mmore-based build (`merge_sources.py`) is kept as fallback; its last output is `out/unified_output.mmore.jsonl`.
- `verify_output.py` (CPU, senv python; `main(unified, report, review_path)`, `coverage()`): checks `out/unified_output.jsonl` against the PDF text layer (word/number coverage per page, figure accounting, leftovers) -> `out/completeness_report.json`, `out/review.html`. `merge_sources.py` also uses the text layer to repair dropped range dashes, changed comparators and lost 10^9 exponents in mmore text (needs senv python for pymupdf).
- `out/`: all generated outputs; `logs/`: job logs
- `main.py`: empty

## Model decisions
- qwen2-vl-72b is dropped (slow, ~17 min load, runaway generations). Use Qwen3-VL-8B (`/mnt/mahdipou/models/Qwen3-VL-8B-Instruct`).
- Qwen3-VL can loop forever on empty table rows. Always use `repetition_penalty≈1.05`, a modest `max_new_tokens`, and loop detection (see `StopOnLoop` in `fill_gaps.py`).
- Qwen3-VL cannot read Khmer. It just echoes the garbled OCR.

## Gap filling (`fill_gaps.py`), status as of 2026-11-19
1. `python fill_gaps.py --prep` (login node) -> `out/gaps.json`: 198 gaps (184 `<!-- image -->`, 13 garbled/Khmer blocks, 1 formula), each mapped to a page by text matching.
2. Pass 1, single page: `fill_gaps.py --shard i --num-shards 2` -> `out/gaps_shard{0,1}.jsonl`. **Done.**
3. Pass 2, 3-page window for gaps that came back `[NOT FOUND]`: `fill_gaps.py --window --batch-size 4 --shard i --num-shards 2` -> `out/gapswin_shard*.jsonl`. **Done 2026-11-19**: only 11/109 came back with content (+8 filled after merge). Spot check (gap 31, p38): the `<!-- image -->` was decorative clip-art whose flowchart text Docling already captured, so many NOT FOUNDs are probably harmless.
4. Pass 3, figure pass: `fill_gaps.py --figures --batch-size 4 --shard i --num-shards 2` -> `out/figpages_shard*.jsonl`. **Done 2026-11-19.** Targets the 43 unfilled image gaps with an Algorithm/Figure/Table caption next to them. It transcribes every graphic on pages p-2..p+2 (157 pages) with no NOT FOUND option. The merge then assigns figures to gaps: the title must match the caption (>=0.6), the label numbers must agree, and the figure must add new text. Bodies that are only `[Image: ...]` descriptions or ECG-machine settings are dropped. Decisions are logged in `out/figassign.json`.
5. `python fill_gaps.py --merge` -> `out/ocr_filled.md`. Currently **107/198 gaps filled** (24 of them by the figure pass, marked `(figure pass)`). Earlier merges are backed up as `out/ocr_filled.pass1.md` and `out/ocr_filled.pass2.md`. Filled blocks are wrapped in `<!-- qwen3 fill: kind, page N -->` ... `<!-- /qwen3 fill -->`. Gaps that are skipped are left as they were: NOT FOUND, looped, echoed, Khmer, unconfident front matter, or an unmatched figure. Unmatched captioned gaps that may need manual work: 33, 64, 78, 81, 101, 103, 112, 119, 122, 124, 170, 173, 178, 195.

Submit: `bash ../config/submit_H.sh h200 <job> "/mnt/mahdipou/ml/fill_gaps.py <args>" 1 8`

## Cluster context (EPFL RCP)
- On the login node this directory is `/mnt/upschrimpf2/scratch/mahdipou/ml`. Inside runai containers it's `/mnt/mahdipou/ml` (the PVC is mounted at `/mnt/`).
- Conda env: `senv` (see `../environment.yml`). Miniconda is at `../miniconda3`.
- Shared HF cache: `../hf_cache`. Local model copies: `../models`.
- Never run model or GPU code on the login node. Submit it through runai (`../config/submit_H.sh`) and watch with `runai logs <job_name> -f`.
- Jobs submitted right after deleting others sometimes stay at status "Unknown" with no pods. Delete them and submit again.
- Container logs use UTC timestamps; the login node uses CET.
- The login node has no poppler (`pdftoppm`) installed.

## Conventions
- Keep paths relative to the project root, or derive them from one root variable, so the same code runs on the login node and in containers.
- Put generated outputs in `out/`, never in `data/`.
