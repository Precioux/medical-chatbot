#!/usr/bin/env python
"""Whole-document OCR of data/source.pdf with Chandra or dots.ocr (one model per job).

    python ocr_models.py --model chandra      # datalab-to/chandra (Qwen3-VL, 9B)
    python ocr_models.py --model dots         # rednote-hilab/dots.ocr (3B)

Loads the model once and loops over the cached 200-DPI page renders in pages/
(any missing page is rendered with extract_pages.render_page). Resumable: pages
already in out/{model}_pages.jsonl are skipped.

Outputs:
  out/{model}_pages.jsonl   {"page": N, "content": "...", "has_table": bool, ...}
  out/{model}_output.md     all pages, joined with <!-- PAGE N --> markers

dots.ocr is run with its official "layout all" prompt, which returns a JSON list of
layout cells. "content" is the cells' text in the model's reading order (tables stay
HTML, the same as dots.ocr's own layoutjson2md). The raw JSON string is kept in "raw".
"""
import argparse
import json
import os
import re
import time

from extract_pages import log, render_page
import extract_pages

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(os.path.dirname(ROOT), "models")
PDF = os.path.join(ROOT, "data", "source.pdf")
PAGES_DIR = os.path.join(ROOT, "pages")
OUT = os.path.join(ROOT, "out")
N_PAGES = 474

CHANDRA_PROMPT = ("Convert this document page to markdown. "
                  "Preserve all tables, figures, and formatting exactly.")

# dots.ocr prompt_layout_all_en (from the model card / dots_ocr/utils/prompts.py).
DOTS_PROMPT = """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]

2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].

3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown.

4. Constraints:
    - The output text must be the original text from the image, with no translation.
    - All layout elements must be sorted according to human reading order.

5. Final Output: The entire output must be a single JSON object.
"""

CFG = {
    "chandra": dict(path=os.path.join(MODELS, "chandra"), prompt=CHANDRA_PROMPT),
    # Directory must not contain a "." (transformers remote-code module naming).
    "dots": dict(path=os.path.join(MODELS, "DotsOCR"), prompt=DOTS_PROMPT),
}

TABLE_RE = re.compile(r"(<table\b)|(^(?=.*\|)[ \t|:-]*-{3,}[ \t|:-]*$)", re.M | re.I)


def has_table(text):
    return bool(TABLE_RE.search(text))


def load(name):
    import torch
    from transformers import AutoProcessor

    path = CFG[name]["path"]
    t0 = time.time()
    if name == "chandra":
        from transformers import AutoModelForImageTextToText
        model = AutoModelForImageTextToText.from_pretrained(
            path, dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
        processor = AutoProcessor.from_pretrained(path)
    else:
        from transformers import AutoConfig, AutoModelForCausalLM
        try:
            import flash_attn  # noqa: F401
            attn = "flash_attention_2"
        except ImportError:
            attn = "sdpa"  # flash-attn is not installed in senv; sdpa is the fallback
        config = AutoConfig.from_pretrained(path, trust_remote_code=True)
        config.vision_config.attn_implementation = attn
        model = AutoModelForCausalLM.from_pretrained(
            path, config=config, dtype=torch.bfloat16, device_map="cuda",
            attn_implementation=attn, trust_remote_code=True)
        log(f"dots.ocr attention: {attn}")
        try:
            processor = AutoProcessor.from_pretrained(path, trust_remote_code=True)
        except Exception as e:  # DotsVLProcessor predates the video_processor arg
            log(f"AutoProcessor failed ({type(e).__name__}: {e}); building it by hand")
            from transformers import AutoTokenizer, Qwen2_5_VLProcessor, Qwen2VLImageProcessor
            from transformers.models.qwen2_vl.video_processing_qwen2_vl import Qwen2VLVideoProcessor
            tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
            processor = Qwen2_5_VLProcessor(
                image_processor=Qwen2VLImageProcessor.from_pretrained(path),
                tokenizer=tok, video_processor=Qwen2VLVideoProcessor(),
                chat_template=json.load(open(os.path.join(path, "chat_template.json")))["chat_template"])
            processor.image_token = "<|imgpad|>"
            processor.image_token_id = 151665
    model.eval()
    processor.tokenizer.padding_side = "left"
    log(f"Loaded {path} in {(time.time() - t0) / 60:.1f} min")
    return model, processor


TAG_RE = re.compile(r"<[^>]{0,200}>")


def is_looping(tail):
    """True if decoded output is stuck repeating itself.

    HTML tags and markdown separator rows are stripped first, so table markup never counts
    as repetition. Then: the last 6 lines with >= 15 characters of text are identical
    (consecutive, so repeated cell values in a real table don't count), or the last 120 characters occur >= 6 times (catches loops
    inside one long line, e.g. dots.ocr's single-line JSON or rows of leader dots)."""
    text = TAG_RE.sub(" ", tail)
    text = re.sub(r"(?m)^[ \t|:-]*-{3,}[ \t|:-]*$", " ", text)  # markdown table separator rows
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.split("\n")]
    lines = [l for l in lines if len(l) >= 15]
    if len(lines) >= 6 and len(set(lines[-6:])) == 1:  # same line 6x in a row
        return True
    flat = re.sub(r"\s+", " ", text).strip()
    return len(flat) > 1000 and flat.count(flat[-120:]) >= 6


def make_stop_on_loop(tok, n_prompt):
    import torch
    from transformers import StoppingCriteria

    class StopOnLoop(StoppingCriteria):
        """Stop a sequence when is_looping() says so. Checked every 32 tokens on the last
        3000 tokens (Khmer costs several tokens per character)."""
        def __call__(self, input_ids, scores, **kw):
            stop = torch.zeros(input_ids.shape[0], dtype=torch.bool, device=input_ids.device)
            n_gen = input_ids.shape[1] - n_prompt
            if n_gen % 32 or n_gen < 256:
                return stop
            for b, seq in enumerate(input_ids[:, n_prompt:]):
                if is_looping(tok.decode(seq[-3000:], skip_special_tokens=True)):
                    stop[b] = True
            return stop

    return StopOnLoop()



def generate(model, processor, prompt, image_paths, max_new_tokens):
    import torch
    from PIL import Image
    from transformers import StoppingCriteriaList

    msg = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
    images = [Image.open(p).convert("RGB") for p in image_paths]
    inputs = processor(text=[text] * len(images), images=images, padding=True,
                       return_tensors="pt").to(model.device)
    n_prompt = inputs.input_ids.shape[1]
    with torch.inference_mode():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.05,
            stopping_criteria=StoppingCriteriaList([make_stop_on_loop(processor.tokenizer, n_prompt)]))
    out = out[:, n_prompt:]
    # Generated length = tokens before the first eos/pad (finished rows are padded with eos).
    stop_ids = model.generation_config.eos_token_id
    stop_ids = set(stop_ids if isinstance(stop_ids, list) else [stop_ids])
    stop_ids |= {processor.tokenizer.pad_token_id, model.generation_config.pad_token_id}
    stop_ids.discard(None)
    n_tok = []
    for o in out.tolist():
        n_tok.append(next((k for k, t in enumerate(o) if t in stop_ids), len(o)))
    texts = processor.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return texts, n_tok


def dots_to_markdown(raw):
    """dots.ocr layout JSON -> text of each cell in reading order. None if not parseable."""
    try:
        cells = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(cells, dict):
        cells = cells.get("layout", cells.get("elements", [cells]))
    parts = []
    for c in cells if isinstance(cells, list) else []:
        if not isinstance(c, dict):
            continue
        t = (c.get("text") or "").strip()
        if c.get("category") == "Picture" or not t:
            continue
        if c.get("category") == "Formula" and not t.startswith("$"):
            t = f"$$\n{t}\n$$"
        parts.append(t)
    return "\n\n".join(parts)


def write_md(model_name, jsonl):
    recs = {}
    for line in open(jsonl):
        r = json.loads(line)
        recs[r["page"]] = r
    md = os.path.join(OUT, f"{model_name}_output.md")
    with open(md + ".part", "w") as f:
        for p in sorted(recs):
            f.write(f"<!-- PAGE {p} -->\n\n{recs[p]['content'].strip()}\n\n")
    os.replace(md + ".part", md)
    log(f"Wrote {md} ({len(recs)} pages)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=CFG, required=True)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=8192)
    ap.add_argument("--pages", default=None, help="e.g. 43 or 40-45 (default: all)")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    extract_pages.LOG_FILE = os.path.join(ROOT, "logs", f"ocr_{args.model}.log")
    jsonl = os.path.join(OUT, f"{args.model}_pages.jsonl")

    if args.pages:
        a, _, b = args.pages.partition("-")
        pages = list(range(int(a), int(b or a) + 1))
    else:
        pages = list(range(1, N_PAGES + 1))
    done = set()
    if os.path.exists(jsonl):
        done = {json.loads(l)["page"] for l in open(jsonl) if l.strip()}
    todo = [p for p in pages if p not in done]
    log(f"{args.model}: {len(todo)} pages to do ({len(done)} already in {jsonl})")
    if not todo:
        write_md(args.model, jsonl)
        return

    model, processor = load(args.model)
    prompt, bs = CFG[args.model]["prompt"], args.batch_size
    t0, n_done = time.time(), 0
    with open(jsonl, "a") as fout:
        for i in range(0, len(todo), bs):
            batch = todo[i:i + bs]
            paths = [render_page(PDF, p, PAGES_DIR, 200) for p in batch]
            tb = time.time()
            texts, n_tok = generate(model, processor, prompt, paths, args.max_new_tokens)
            for p, t, n in zip(batch, texts, n_tok):
                rec = {"page": p}
                if args.model == "dots":
                    md = dots_to_markdown(t)
                    rec.update(content=md if md is not None else t, raw=t, json_ok=md is not None)
                else:
                    rec["content"] = t
                rec.update(has_table=has_table(rec["content"]), n_tokens=n,
                           hit_max=n >= args.max_new_tokens, model=args.model)
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            n_done += len(batch)
            rate = (time.time() - t0) / n_done
            eta = rate * (len(todo) - n_done)
            log(f"pages {batch[0]}-{batch[-1]} ({n_done}/{len(todo)}) {time.time() - tb:.0f}s "
                f"tokens={n_tok} | {rate:.1f} s/page, ETA {eta / 3600:.1f} h")
    write_md(args.model, jsonl)
    log("DONE")


if __name__ == "__main__":
    main()
