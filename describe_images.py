#!/usr/bin/env python
"""Part 1: describe the non-decorative pictures Docling found, with Qwen3-VL-8B.

    python describe_images.py --crop-only      # login node OK: just write the crops (no model)
    python describe_images.py                  # GPU (runai, see job_images.sh): crops + descriptions
    python describe_images.py --limit 5        # quick test

Pictures: ocr/output.json "pictures" (184). Bboxes with area < 5000 pt^2 are logos/icons and are skipped.
Page images: the cached 200-DPI renders in pages/ (same as pdftoppm -r 200; pdftoppm is not on the login
node). Bboxes are BOTTOMLEFT-origin PDF points; pages differ in size (A4/Letter/landscape), so each bbox is
scaled by render_size / Docling page size.

Outputs (resumable: pictures already in the jsonl are skipped):
  out/images/page_NNN_figK.png           crops
  out/image_descriptions.jsonl           {"page","bbox","type","description","image_path","picture_ref",...}
  out/image_descriptions_skipped.jsonl   DECORATIVE answers and filtered-out small pictures (for the report)
"""
import argparse, json, os, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCLING = os.path.join(ROOT, "ocr", "output.json")
PAGES = os.path.join(ROOT, "pages")
IMG_DIR = os.path.join(ROOT, "out", "images")
OUT = os.path.join(ROOT, "out", "image_descriptions.jsonl")
SKIPPED = os.path.join(ROOT, "out", "image_descriptions_skipped.jsonl")
MODEL = os.path.join(os.path.dirname(ROOT), "models", "Qwen3-VL-8B-Instruct")
MIN_AREA = 5000      # pt^2
PAD = 10             # px of margin around the crop

PROMPT = """What is in this medical image? Describe in detail:
- If flowchart/algorithm: list all decision points, branches, drug names, dosages, and outcomes
- If diagram/chart: describe components and labels
- If ECG/medical image: describe what it shows clinically
- If table rendered as image: extract as markdown table
- If decorative (logo, icon, clipart): respond DECORATIVE
Keep medical terms in English. Be precise with numbers.
Start your answer with one line "TYPE: <flowchart|diagram|chart|ecg|medical_image|table|photo|decorative|other>"."""
TYPES = {"flowchart", "diagram", "chart", "ecg", "medical_image", "table", "photo", "decorative", "other"}


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def pictures():
    """All Docling pictures -> list of dicts with page, bbox, area, figure index on its page."""
    d = json.load(open(DOCLING))
    sizes = {int(k): v["size"] for k, v in d["pages"].items()}
    out, per_page = [], {}
    for p in d["pictures"]:
        pr = p["prov"][0]
        b, pg = pr["bbox"], pr["page_no"]
        per_page[pg] = per_page.get(pg, 0) + 1
        out.append({"picture_ref": p["self_ref"], "page": pg, "fig": per_page[pg], "bbox": b,
                    "page_size": sizes[pg], "area": (b["r"] - b["l"]) * abs(b["t"] - b["b"])})
    return out


def crop(pic):
    from PIL import Image
    img = Image.open(os.path.join(PAGES, f"page_{pic['page']:04d}.png"))
    W, H = img.size
    sx, sy = W / pic["page_size"]["width"], H / pic["page_size"]["height"]
    b = pic["bbox"]
    if b.get("coord_origin", "BOTTOMLEFT") == "BOTTOMLEFT":
        top, bot = pic["page_size"]["height"] - b["t"], pic["page_size"]["height"] - b["b"]
    else:
        top, bot = b["t"], b["b"]
    box = (max(0, int(b["l"] * sx) - PAD), max(0, int(top * sy) - PAD),
           min(W, int(b["r"] * sx) + PAD), min(H, int(bot * sy) + PAD))
    rel = f"images/page_{pic['page']:03d}_fig{pic['fig']}.png"
    path = os.path.join(ROOT, "out", rel)
    if not os.path.exists(path):
        img.crop(box).save(path)
    return rel, path


def parse(text):
    """'TYPE: flowchart\\n...' -> ('flowchart', body). DECORATIVE anywhere as the whole answer -> decorative."""
    t = text.strip()
    m = re.match(r"(?i)\**\s*type\s*:\s*\**\s*([a-z_ ]+)\**\s*\n?", t)
    typ, body = (m.group(1).strip().lower().replace(" ", "_"), t[m.end():].strip()) if m else ("other", t)
    if typ not in TYPES:
        typ = "other"
    if re.fullmatch(r"(?i)[\W_]*decorative[\W_]*", body) or (typ == "decorative" and len(body) < 200):
        typ = "decorative"
    return typ, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=1500)
    a = ap.parse_args()
    os.makedirs(IMG_DIR, exist_ok=True)

    pics = pictures()
    keep = [p for p in pics if p["area"] >= MIN_AREA]
    small = [p for p in pics if p["area"] < MIN_AREA]
    log(f"{len(pics)} pictures, {len(small)} below {MIN_AREA} pt^2 (decorative), {len(keep)} to describe")
    for p in keep:
        p["image_path"], p["abs_path"] = crop(p)
    if a.crop_only:
        log(f"crops written to {IMG_DIR}")
        return

    done = set()
    for f in (OUT, SKIPPED):
        if os.path.exists(f):
            done |= {json.loads(l)["picture_ref"] for l in open(f)}
    if not os.path.exists(SKIPPED) or not any('"reason": "small"' in l for l in open(SKIPPED)):
        with open(SKIPPED, "a") as f:
            for p in small:
                f.write(json.dumps({"picture_ref": p["picture_ref"], "page": p["page"], "bbox": p["bbox"],
                                    "area": round(p["area"]), "reason": "small"}) + "\n")
    todo = [p for p in keep if p["picture_ref"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    log(f"{len(todo)} left to describe")
    if not todo:
        return

    os.environ["USE_TF"] = "0"
    import torch
    from transformers import StoppingCriteria, StoppingCriteriaList
    from extract_pages import load_model, load_image
    model, processor = load_model(MODEL, "bf16")
    tok = processor.tokenizer

    class StopOnLoop(StoppingCriteria):
        """Qwen3-VL can repeat empty table rows forever (CLAUDE.md): stop a row whose last 400 chars
        already occur >= 4 times in its output."""
        def __init__(self, n_prompt):
            self.n_prompt = n_prompt
        def __call__(self, input_ids, scores, **kw):
            if (input_ids.shape[1] - self.n_prompt) % 32:
                return torch.zeros(input_ids.shape[0], dtype=torch.bool, device=input_ids.device)
            res = []
            for row in input_ids[:, self.n_prompt:]:
                t = tok.decode(row[-1500:], skip_special_tokens=True)
                res.append(len(t) > 1200 and t.count(t[-400:]) >= 4)
            return torch.tensor(res, dtype=torch.bool, device=input_ids.device)

    msg = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
    chat = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
    t_start, n_done = time.time(), 0
    for s in range(0, len(todo), a.batch_size):
        batch = todo[s:s + a.batch_size]
        images = [load_image(p["abs_path"], 1600 * 1600) for p in batch]
        inputs = processor(text=[chat] * len(batch), images=images, padding=True, return_tensors="pt").to(model.device)
        n_prompt = inputs.input_ids.shape[1]
        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False, repetition_penalty=1.05,
                                 stopping_criteria=StoppingCriteriaList([StopOnLoop(n_prompt)]))
        out = out[:, n_prompt:]
        texts = processor.batch_decode(out, skip_special_tokens=True)
        for p, t, o in zip(batch, texts, out):
            n_tok = int((o != tok.pad_token_id).sum())
            typ, body = parse(t)
            rec = {"picture_ref": p["picture_ref"], "page": p["page"], "bbox": p["bbox"], "type": typ,
                   "description": body, "image_path": p["image_path"], "n_tok": n_tok,
                   "hit_max": n_tok >= a.max_new_tokens}
            if typ == "decorative":
                rec["reason"] = "model said DECORATIVE"
                with open(SKIPPED, "a") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            else:
                with open(OUT, "a") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_done += len(batch)
        el = time.time() - t_start
        eta = el / n_done * (len(todo) - n_done)
        log(f"pages {[p['page'] for p in batch]}: types {[parse(t)[0] for t in texts]} | "
            f"{n_done}/{len(todo)} done, {el / 60:.1f} min elapsed, ~{eta / 60:.1f} min left")
    log("done")


if __name__ == "__main__":
    main()
