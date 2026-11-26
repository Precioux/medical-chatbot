#!/usr/bin/env python
"""Extract every page of data/source.pdf with Qwen2-VL-72B (text + markdown tables).

Parallel layout: N runai jobs, each run with --shard i --num-shards N, take
interleaved pages (i, i+N, i+2N, ...), write out/pages_shard{i}.jsonl and log to
logs/extraction_s{i}.log. Restarting a shard skips pages already written.
When all shards are done:  python extract_pages.py --merge
  -> pages_extracted.jsonl  ({"page", "content", "has_table"} per line, page order)
  -> output.md              (all pages, separated by <!-- PAGE n --> markers)
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT = """You are a medical document parser. Extract ALL content from this page.
- For regular text: output it as plain text with section headings marked as ##
- For tables: output them as markdown tables, preserving EVERY row, column, merged cell, and value exactly. Pay special attention to symbols like ≤ ≥ and all numbers, drug names, and dosages.
- For lists: preserve numbered/bulleted structure
Output the page content in order from top to bottom."""

# Exact table prompt requested by the user (rerun of table pages, 2026-11-19).
TABLE_PROMPT = """This is a medical scoring/dosage table. Extract it as a markdown table.
CRITICAL RULES:
- The table has EXACTLY as many columns as the header row
- If a cell is empty, write an empty cell ||, NEVER skip it
- NEVER shift values left to fill empty cells
- For merged header cells, repeat the header text
- Preserve ≤ ≥ symbols and all numbers exactly
- Output the table and nothing else"""
PROMPTS = {"page": PROMPT, "table": TABLE_PROMPT}

LOG_FILE = None


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOG_FILE:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")


def num_pages(pdf):
    import pymupdf
    with pymupdf.open(pdf) as d:
        return d.page_count


def render_page(pdf, page_no, img_dir, dpi):
    """Render 1-based page_no to PNG once (cached). pdftoppm if installed, else PyMuPDF (same DPI)."""
    path = os.path.join(img_dir, f"page_{page_no:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    tmp = path + f".tmp{os.getpid()}"
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(page_no),
                        "-l", str(page_no), "-singlefile", pdf, tmp], check=True)
    else:
        import pymupdf
        with pymupdf.open(pdf) as d:
            d[page_no - 1].get_pixmap(dpi=dpi).save(tmp + ".png")
    os.replace(tmp + ".png", path)
    return path


TABLE_SEP = re.compile(r"^(?=.*\|)[ \t|:-]*-{3,}[ \t|:-]*$", re.M)


def has_table(text):
    return bool(TABLE_SEP.search(text))


def load_model(model_path, dtype_name):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16}[dtype_name]
    log(f"Loading {model_path} ({dtype_name}, device_map=auto) on "
        f"{torch.cuda.device_count()} GPU(s)...")
    t0 = time.time()
    # Auto class covers Qwen2-VL and Qwen3-VL (transformers >= 4.57).
    model = AutoModelForImageTextToText.from_pretrained(
        model_path, dtype=dtype, device_map="auto", attn_implementation="sdpa",
    ).eval()
    processor = AutoProcessor.from_pretrained(model_path)
    processor.tokenizer.padding_side = "left"
    log(f"Model loaded in {(time.time() - t0) / 60:.1f} min")
    return model, processor


def load_image(path, max_pixels):
    from PIL import Image
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w * h > max_pixels:
        f = (max_pixels / (w * h)) ** 0.5
        img = img.resize((int(w * f), int(h * f)), Image.LANCZOS)
    return img


def generate(model, processor, image_paths, max_new_tokens, max_pixels, prompt=PROMPT):
    import torch

    msg = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
    texts = [text] * len(image_paths)
    images = [load_image(p, max_pixels) for p in image_paths]
    inputs = processor(text=texts, images=images, padding=True, return_tensors="pt")
    inputs = inputs.to(model.device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    out = out[:, inputs.input_ids.shape[1]:]
    n_tok = [(o != processor.tokenizer.pad_token_id).sum().item() for o in out]
    return processor.batch_decode(out, skip_special_tokens=True), n_tok


def merge(out_dir, pdf):
    recs = {}
    for fn in sorted(glob.glob(os.path.join(out_dir, "pages_shard*.jsonl"))):
        with open(fn) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                recs[r["page"]] = r
    total = num_pages(pdf)
    missing = [p for p in range(1, total + 1) if p not in recs]
    with open(os.path.join(ROOT, "pages_extracted.jsonl"), "w") as fj, \
         open(os.path.join(ROOT, "output.md"), "w") as fm:
        for p in sorted(recs):
            r = recs[p]
            fj.write(json.dumps({"page": p, "content": r["content"],
                                 "has_table": r["has_table"]}, ensure_ascii=False) + "\n")
            fm.write(f"<!-- PAGE {p} -->\n\n{r['content'].strip()}\n\n")
    trunc = sorted(p for p, r in recs.items() if r.get("truncated"))
    print(f"{len(recs)}/{total} pages merged; {sum(r['has_table'] for r in recs.values())} "
          f"with tables")
    print(f"missing pages ({len(missing)}): {missing}")
    print(f"hit max_new_tokens, check these ({len(trunc)}): {trunc}")


def main():
    global LOG_FILE
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=os.path.join(ROOT, "data/source.pdf"))
    ap.add_argument("--model", default="/mnt/mahdipou/models/qwen2-vl-72b")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "out"))
    ap.add_argument("--img-dir", default=os.path.join(ROOT, "pages"))
    ap.add_argument("--log-dir", default=os.path.join(ROOT, "logs"))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--pages", default=None, help="subset, e.g. 1-10 or 43,44 (for tests)")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--dtype", choices=["bf16", "fp16"], default="bf16")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--max-pixels", type=int, default=1700 * 2400)  # full 200-DPI A4 page
    ap.add_argument("--merge", action="store_true", help="combine shard outputs and exit")
    ap.add_argument("--mode", choices=["page", "table"], default="page",
                    help="page = full-page prompt; table = strict table prompt")
    ap.add_argument("--table-pages", action="store_true",
                    help="only pages with has_table=true in pages_extracted.jsonl")
    ap.add_argument("--tag", default="pages", help="output/log name prefix")
    args = ap.parse_args()

    if args.merge:
        merge(args.out_dir, args.pdf)
        return

    # torch (incl. _dynamo) MUST be imported before pymupdf: the other order breaks
    # torch._dynamo's import inside the runai container (NP_SUPPORTED_MODULES ImportError).
    import torch, torch._dynamo  # noqa: F401,E401
    import transformers  # noqa: F401

    for d in (args.out_dir, args.img_dir, args.log_dir):
        os.makedirs(d, exist_ok=True)
    LOG_FILE = os.path.join(args.log_dir, f"{args.tag}_s{args.shard}.log"
                            if args.tag != "pages" else f"extraction_s{args.shard}.log")

    total = num_pages(args.pdf)
    if args.pages:
        pages = []
        for part in args.pages.split(","):
            a, _, b = part.partition("-")
            pages += list(range(int(a), int(b or a) + 1))
    else:
        pages = list(range(1, total + 1))
    if args.table_pages:
        with open(os.path.join(ROOT, "pages_extracted.jsonl")) as f:
            tp = {r["page"] for r in map(json.loads, f) if r["has_table"]}
        pages = [p for p in pages if p in tp]
    my_pages = pages[args.shard::args.num_shards]

    out_path = os.path.join(args.out_dir, f"{args.tag}_shard{args.shard}.jsonl")
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["page"])
                except Exception:
                    pass
    todo = [p for p in my_pages if p not in done]
    log(f"shard {args.shard}/{args.num_shards}: {len(my_pages)} of {total} pages, "
        f"{len(my_pages) - len(todo)} already done, {len(todo)} to do")
    if not todo:
        return

    log(f"Rendering {len(todo)} pages at {args.dpi} DPI "
        f"({'pdftoppm' if shutil.which('pdftoppm') else 'PyMuPDF'})...")
    imgs = {p: render_page(args.pdf, p, args.img_dir, args.dpi) for p in todo}
    log("Rendering done")

    model, processor = load_model(args.model, args.dtype)

    t_start, n_done, bs, i = time.time(), 0, args.batch_size, 0
    with open(out_path, "a") as fout:
        while i < len(todo):
            batch = todo[i:i + bs]
            log(f"processing pages {batch} ({i + 1}-{i + len(batch)} of {len(todo)})")
            t0 = time.time()
            try:
                responses, n_tok = generate(model, processor, [imgs[p] for p in batch],
                                            args.max_new_tokens, args.max_pixels,
                                            PROMPTS[args.mode])
            except Exception as e:  # mostly CUDA OOM: halve batch and retry
                import torch
                torch.cuda.empty_cache()
                if bs > 1:
                    bs = max(1, bs // 2)
                    log(f"  {type(e).__name__}: {str(e)[:200]} -> batch size {bs}")
                    continue
                log(f"  FAILED page {batch[0]}: {e}; skipping (rerun the shard to retry)")
                i += 1
                continue

            for p, text, nt in zip(batch, responses, n_tok):
                rec = {"page": p, "mode": args.mode, "model": args.model, "content": text, "has_table": has_table(text),
                       "n_tokens": nt, "truncated": nt >= args.max_new_tokens}
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if rec["truncated"]:
                    log(f"  page {p}: hit max_new_tokens ({nt}), output may be cut")
            fout.flush()
            n_done += len(batch)
            i += len(batch)
            el = time.time() - t_start
            eta = el / n_done * (len(todo) - n_done)
            log(f"  batch {time.time() - t0:.0f}s ({sum(n_tok)} tokens); "
                f"{n_done}/{len(todo)} pages done, ETA {eta / 60:.0f} min")
    log(f"Shard {args.shard} finished -> {out_path}")


if __name__ == "__main__":
    main()
