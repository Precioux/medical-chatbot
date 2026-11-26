#!/usr/bin/env python
"""Re-extract every Docling table from source.pdf with Qwen2-VL-72B.

Parallel layout: run N copies with --shard i --num-shards N. Each shard takes a
disjoint set of pages, writes out/tables_shard{i}.jsonl and resumes from that
file if restarted. merge_tables.py combines the shards into tables_extracted.jsonl.

Paths default to the container view (/mnt/mahdipou/...).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT = (
    "Extract ALL tables on this page as markdown tables. "
    "Preserve every row, column, merged cell, and value exactly. "
    "Pay special attention to symbols like ≤ and ≥ and all numbers."
)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- Docling input
def load_tables(json_path):
    """Return [(global_table_index, [page_no, ...]), ...] in Docling order."""
    with open(json_path) as f:
        doc = json.load(f)
    tables = doc.get("tables")
    if tables is None:
        sys.exit(f"No 'tables' key in {json_path}; top-level keys: {list(doc)}")
    out = []
    for i, t in enumerate(tables):
        pages = sorted({p["page_no"] for p in t.get("prov", []) if "page_no" in p})
        if not pages:
            log(f"WARNING table {i} has no prov/page_no; skipped")
            continue
        out.append((i, pages))
    return out


# ---------------------------------------------------------------- rasterising
def render_page(pdf, page_no, img_dir, dpi):
    """Render 1-based page_no to PNG once (cached on disk). pdftoppm if present, else PyMuPDF."""
    path = os.path.join(img_dir, f"page_{page_no:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    tmp = path + f".tmp{os.getpid()}"
    if shutil.which("pdftoppm"):
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page_no), "-l", str(page_no),
             "-singlefile", pdf, tmp],
            check=True,
        )
        os.replace(tmp + ".png", path)
    else:
        import pymupdf
        with pymupdf.open(pdf) as d:
            d[page_no - 1].get_pixmap(dpi=dpi).save(tmp + ".png")
        os.replace(tmp + ".png", path)
    return path


# ---------------------------------------------------------------- parsing
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")


def split_markdown_tables(text):
    """Return the markdown tables in text, in order of appearance."""
    tables, cur = [], []
    for line in text.splitlines():
        if TABLE_LINE.match(line):
            cur.append(line.rstrip())
        else:
            if cur:
                tables.append("\n".join(cur))
                cur = []
    if cur:
        tables.append("\n".join(cur))
    # keep only real tables (header + separator at least)
    return [t for t in tables if t.count("\n") >= 1]


# ---------------------------------------------------------------- model
def load_model(model_path, dtype_name):
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16}[dtype_name]
    log(f"Loading {model_path} ({dtype_name}, device_map=auto) on "
        f"{torch.cuda.device_count()} GPU(s)...")
    t0 = time.time()
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_path, torch_dtype=dtype, device_map="auto", attn_implementation="sdpa",
    ).eval()
    processor = AutoProcessor.from_pretrained(model_path)
    processor.tokenizer.padding_side = "left"
    log(f"Model loaded in {(time.time() - t0) / 60:.1f} min")
    return model, processor


def generate(model, processor, image_paths, max_new_tokens, max_pixels):
    import torch
    from qwen_vl_utils import process_vision_info

    msgs = [[{"role": "user", "content": [
        {"type": "image", "image": f"file://{p}", "max_pixels": max_pixels},
        {"type": "text", "text": PROMPT},
    ]}] for p in image_paths]
    texts = [processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
             for m in msgs]
    images, _ = process_vision_info(msgs)
    inputs = processor(text=texts, images=images, padding=True, return_tensors="pt")
    inputs = inputs.to(model.device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    out = out[:, inputs.input_ids.shape[1]:]
    return processor.batch_decode(out, skip_special_tokens=True)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=os.path.join(ROOT, "data/source.pdf"))
    ap.add_argument("--json", default=os.path.join(ROOT, "output.json"))
    ap.add_argument("--model", default="/mnt/mahdipou/models/qwen2-vl-72b")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "out"))
    ap.add_argument("--img-dir", default=os.path.join(ROOT, "pages"))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--dtype", choices=["bf16", "fp16"], default="bf16")
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--max-pixels", type=int, default=1700 * 2400)  # full 200-DPI A4 page (1654x2339)
    ap.add_argument("--render-only", action="store_true", help="just rasterise pages, no model")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.img_dir, exist_ok=True)

    model = processor = None
    if not os.path.exists(args.json) and not args.render_only:
        # Docling is still running: use the ~40 min model load to wait for it.
        model, processor = load_model(args.model, args.dtype)
        log(f"Waiting for {args.json} (Docling job)...")
        while not os.path.exists(args.json):
            time.sleep(30)
        log(f"{args.json} found")

    tables = load_tables(args.json)
    by_page = defaultdict(list)  # page -> [global table idx] in Docling order
    for idx, pages in tables:
        for p in pages:
            by_page[p].append(idx)
    all_pages = sorted(by_page)
    log(f"{len(tables)} tables on {len(all_pages)} distinct pages")

    # Balance shards by table count (pages with many tables generate longer outputs).
    loads = [0] * args.num_shards
    assign = defaultdict(list)
    for p in sorted(all_pages, key=lambda p: -len(by_page[p])):
        s = loads.index(min(loads))
        assign[s].append(p)
        loads[s] += len(by_page[p])
    my_pages = sorted(assign[args.shard])

    out_path = os.path.join(args.out_dir, f"tables_shard{args.shard}.jsonl")
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["page"])
                except Exception:
                    pass
    todo = [p for p in my_pages if p not in done]
    log(f"shard {args.shard}/{args.num_shards}: {len(my_pages)} pages, "
        f"{len(done & set(my_pages))} already done, {len(todo)} to do")

    log(f"Rendering {len(todo)} pages at {args.dpi} DPI "
        f"({'pdftoppm' if shutil.which('pdftoppm') else 'PyMuPDF'})...")
    imgs = {p: render_page(args.pdf, p, args.img_dir, args.dpi) for p in todo}
    if args.render_only or not todo:
        log("Done.")
        return

    if model is None:
        model, processor = load_model(args.model, args.dtype)

    t_start, n_done, bs = time.time(), 0, args.batch_size
    i = 0
    with open(out_path, "a") as fout:
        while i < len(todo):
            batch = todo[i:i + bs]
            log(f"pages {batch} ({i + 1}-{i + len(batch)} of {len(todo)})")
            t0 = time.time()
            try:
                responses = generate(model, processor, [imgs[p] for p in batch],
                                     args.max_new_tokens, args.max_pixels)
            except Exception as e:  # mostly CUDA OOM on big batches: halve and retry
                import torch
                torch.cuda.empty_cache()
                if bs > 1:
                    bs = max(1, bs // 2)
                    log(f"  {type(e).__name__}: {str(e)[:200]} -> batch size {bs}")
                    continue
                log(f"  FAILED page {batch[0]}: {e}")
                responses = [f"__ERROR__ {type(e).__name__}: {e}"]

            for p, resp in zip(batch, responses):
                md_tables = split_markdown_tables(resp)
                ids = by_page[p]
                if len(md_tables) != len(ids):
                    log(f"  page {p}: Docling has {len(ids)} table(s), model returned "
                        f"{len(md_tables)}")
                for k, tidx in enumerate(ids):
                    rec = {
                        "page": p,
                        "table_index": tidx,             # index into output.json "tables"
                        "page_table_index": k,           # k-th Docling table on this page
                        "markdown": md_tables[k] if k < len(md_tables) else "",
                        "n_tables_docling": len(ids),
                        "n_tables_model": len(md_tables),
                        "raw_response": resp,
                    }
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
            n_done += len(batch)
            i += len(batch)
            el = time.time() - t_start
            eta = el / n_done * (len(todo) - n_done)
            log(f"  {time.time() - t0:.0f}s for batch; {n_done}/{len(todo)} pages, "
                f"ETA {eta / 60:.0f} min")
    log(f"Shard {args.shard} finished -> {out_path}")


if __name__ == "__main__":
    main()
