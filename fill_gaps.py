#!/usr/bin/env python
"""Fill the parts Docling OCR left out of ocr/output.md using Qwen3-VL-8B.

Gaps = `<!-- image -->`, `<!-- formula-not-decoded -->`, and blocks of garbled /
Khmer OCR text. Each gap is located on a PDF page by matching the surrounding OCR
text against the per-page text in pages_extracted.jsonl (used only as a page index),
then Qwen3 gets the page image + the text before/after the gap and transcribes it.

  1. python fill_gaps.py --prep              (login node, CPU) -> out/gaps.json
  2. N runai jobs: fill_gaps.py --shard i --num-shards N   -> out/gaps_shard{i}.jsonl
     then --window (retry NOT FOUND on p-1..p+1)              -> out/gapswin_shard{i}.jsonl
     then --figures (all figures on pages near captioned gaps) -> out/figpages_shard{i}.jsonl
  3. python fill_gaps.py --merge             (login node)    -> out/ocr_filled.md (+ out/figassign.json)
Restarting a shard skips gaps already written.
"""
import argparse
import collections
import glob
import json
import os
import re
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
GAPS = os.path.join(OUT, "gaps.json")
KHMER = re.compile(r"[ក-៿]")

IMAGE_PROMPT = """This is a page from a medical clinical practice guideline. An OCR system extracted the page text but could NOT read one figure/image region on it.

Text just BEFORE the missing region:
<<<{before}>>>

Text just AFTER the missing region:
<<<{after}>>>

Transcribe the content of the figure/image that sits between these two passages.
- Flowchart/algorithm: write it as a nested markdown list that follows the boxes and arrows (condition -> next step), keeping every word, number and dose.
- Table: output a markdown table with every row and column.
- Text inside the image: transcribe it exactly.
- Only a logo, seal, photo or decoration: output one line: [Image: short description]
If the BEFORE/AFTER text does not appear on this page at all, output exactly: [NOT FOUND]
Do NOT repeat the before/after text. Output only the content, nothing else."""

TEXT_PROMPT = """This is a page from a medical clinical practice guideline. OCR garbled one region of this page into:
<<<{orig}>>>

Text just BEFORE that region:
<<<{before}>>>

Text just AFTER that region:
<<<{after}>>>

Transcribe the original text of that region exactly as printed, in its original language (Khmer and/or English), keeping headings, lists and line structure.\nIf the BEFORE/AFTER text does not appear on this page at all, output exactly: [NOT FOUND]
Do NOT repeat the before/after text. Output only the transcription."""

# pass 3: no "find the gap" question (the model bailed out with NOT FOUND whenever the
# before/after text straddled two pages). Just transcribe every graphic on the page;
# merge() assigns figures to gaps by caption match + novelty.
FIGURE_PROMPT = """This is a page from a medical clinical practice guideline.
Find every graphic element on this page: flowcharts, algorithms, decision trees, diagrams, charts, nomograms, ECG strips, and tables that are drawn as pictures. Ignore ordinary paragraphs, headings and bullet lists of body text.
For each graphic, output:
FIGURE: <its title or caption exactly as printed on the page, or "untitled">
then its content:
- Flowchart/algorithm/decision tree: a nested markdown list that follows the boxes and arrows (condition -> next step), keeping every word, number and dose.
- Table: a markdown table with every row and column.
- Diagram/chart/photo with labels: transcribe all labels and text in it.
- Pure illustration or decoration with no text: one line [Image: short description]
If the page has no graphic element at all, output exactly: NO FIGURE
Output only this, nothing else."""
CAPTION = re.compile(r"algorithm|figure|fig\.|flow ?chart|diagram|table|schema|management", re.I)


# ---------------------------------------------------------------- prep (CPU)
def is_bad_line(s, vocab):
    s = s.strip()
    if s == "<!-- image -->":
        return "image"
    if s == "<!-- formula-not-decoded -->":
        return "formula"
    if s.startswith("|") or s.startswith("<!--") or "http" in s:
        return None  # table rows / links: leave alone
    if KHMER.search(s):
        return "text"
    # garbled OCR: most of its words are unknown to the clean per-page text
    words = re.findall(r"[A-Za-z]{4,}", s)
    if len(words) >= 2 and sum(w.lower() not in vocab for w in words) / len(words) > 0.6:
        return "text"
    return None


def prep():
    md = open(os.path.join(ROOT, "ocr/output.md")).read().split("\n")
    pages = [json.loads(l) for l in open(os.path.join(ROOT, "pages_extracted.jsonl"))]

    def toks(s):
        return re.findall(r"[a-z]{4,}", s.lower())

    idx = collections.defaultdict(set)
    for p in pages:
        t = toks(p["content"])
        for i in range(len(t) - 2):
            idx[" ".join(t[i:i + 3])].add(p["page"])

    # page per line: vote over a +-6 line window, keep only confident votes
    line_page = [None] * len(md)
    for i in range(len(md)):
        t = toks(" ".join(md[max(0, i - 6):i + 7]))
        v = collections.Counter()
        for j in range(len(t) - 2):
            ps = idx.get(" ".join(t[j:j + 3]))
            if ps and len(ps) <= 3:
                v.update(ps)
        if v and v.most_common(1)[0][1] >= 3:
            line_page[i] = v.most_common(1)[0][0]
    # fill holes from neighbours (document order ~ page order)
    last, confident = 1, []
    for i in range(len(md)):
        confident.append(line_page[i] is not None)
        if line_page[i] is None:
            line_page[i] = last
        last = line_page[i]

    # group consecutive bad lines (blank lines in between allowed) into gaps
    vocab = {w for p in pages for w in re.findall(r"[a-z]{4,}", p["content"].lower())}
    kinds = [is_bad_line(l, vocab) for l in md]
    gaps, i = [], 0
    while i < len(md):
        k = kinds[i]
        if not k:
            i += 1
            continue
        j = i
        if k == "text":  # merge a run of garbled lines
            while True:
                n = j + 1
                while n < len(md) and not md[n].strip():
                    n += 1
                if n < len(md) and kinds[n] == "text":
                    j = n
                else:
                    break
        good_before = [l for l, kk in zip(md[:i], kinds[:i]) if not kk and l.strip()]
        good_after = [l for l, kk in zip(md[j + 1:], kinds[j + 1:]) if not kk and l.strip()]
        gaps.append({
            "id": len(gaps), "start": i, "end": j, "kind": k,
            "page": line_page[i], "confident": confident[i],
            "orig": "\n".join(md[i:j + 1]),
            "before": "\n".join(good_before[-4:])[-500:],
            "after": "\n".join(good_after[:4])[:500],
        })
        i = j + 1
    json.dump(gaps, open(GAPS, "w"), ensure_ascii=False, indent=1)
    c = collections.Counter(g["kind"] for g in gaps)
    print(f"{len(gaps)} gaps {dict(c)} on {len({g['page'] for g in gaps})} pages -> {GAPS}")


# ---------------------------------------------------------------- run (GPU)
def run(args):
    import torch, torch._dynamo  # noqa: F401,E401  (must come before pymupdf)
    from transformers import StoppingCriteria, StoppingCriteriaList
    import extract_pages as ep

    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    ep.LOG_FILE = os.path.join(ROOT, "logs", f"{'gapswin' if args.window else 'figpages' if args.figures else 'gaps'}_s{args.shard}.log")
    gaps = json.load(open(GAPS))
    if args.window:  # second pass: only gaps whose single-page answer was NOT FOUND
        nf = {r["id"] for r in load_results("gaps_shard") if "[NOT FOUND]" in r["content"]}
        gaps = [g for g in gaps if g["id"] in nf]
    if args.figures:  # third pass: one item per candidate page (id = page number)
        gaps = [{"id": p, "page": p, "kind": "figpage"} for p in figure_pages(figure_targets())]
    gaps = gaps[args.shard::args.num_shards]
    tag = "gapswin" if args.window else "figpages" if args.figures else "gaps"
    out_path = os.path.join(OUT, f"{tag}_shard{args.shard}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    todo = [g for g in gaps if g["id"] not in done]
    ep.log(f"shard {args.shard}/{args.num_shards}: {len(gaps)} gaps, {len(todo)} to do")
    if not todo:
        return
    model, processor = ep.load_model(args.model, "bf16")
    tok = processor.tokenizer

    class StopOnLoop(StoppingCriteria):
        """Stop a sequence once one non-trivial line repeats >= 6 times in its tail."""
        def __init__(self, n_prompt):
            self.n_prompt = n_prompt

        def __call__(self, input_ids, scores, **kw):
            stop = torch.zeros(input_ids.shape[0], dtype=torch.bool, device=input_ids.device)
            if (input_ids.shape[1] - self.n_prompt) % 32:
                return stop
            for b, seq in enumerate(input_ids[:, self.n_prompt:]):
                lines = [l.strip() for l in tok.decode(seq[-400:]).split("\n") if l.strip()]
                if lines and collections.Counter(lines[-30:]).most_common(1)[0][1] >= 6:
                    stop[b] = True
            return stop

    t0, bs = time.time(), args.batch_size
    with open(out_path, "a") as fout:
        for i in range(0, len(todo), bs):
            batch = todo[i:i + bs]
            ep.log(f"gaps {[g['id'] for g in batch]} pages {[g['page'] for g in batch]} "
                   f"({i + len(batch)}/{len(todo)})")
            texts, images = [], []
            for g in batch:
                if g["kind"] == "figpage":
                    p = FIGURE_PROMPT
                else:
                    p = (IMAGE_PROMPT if g["kind"] in ("image", "formula") else TEXT_PROMPT)
                    p = p.format(before=g["before"], after=g["after"], orig=g["orig"][:1500])
                pgs = ([q for q in (g["page"] - 1, g["page"], g["page"] + 1) if 1 <= q <= 474]
                       if args.window else [g["page"]])
                if args.window:
                    p = (f"These are {len(pgs)} consecutive pages ({', '.join(map(str, pgs))}) of the "
                         "document; the region may be on any of them. Start your answer with a line "
                         "'PAGE: <n>' giving the page it is on.\n\n"
                         + p.replace("this page", "these pages").replace("This is a page", "These are pages"))
                msg = [{"role": "user", "content": [{"type": "image"}] * len(pgs) + [{"type": "text", "text": p}]}]
                texts.append(processor.apply_chat_template(msg, tokenize=False,
                                                           add_generation_prompt=True))
                images.append([ep.load_image(
                    ep.render_page(os.path.join(ROOT, "data/source.pdf"), q,
                                   os.path.join(ROOT, "pages"), 200), args.max_pixels)
                    for q in pgs])
            inputs = processor(text=texts, images=images, padding=True,
                               return_tensors="pt").to(model.device)
            n_prompt = inputs.input_ids.shape[1]
            tb = time.time()
            with torch.inference_mode():
                out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                                     do_sample=False, repetition_penalty=1.05,
                                     stopping_criteria=StoppingCriteriaList([StopOnLoop(n_prompt)]))
            out = out[:, n_prompt:]
            for g, o in zip(batch, out):
                n = int((o != tok.pad_token_id).sum())
                text = tok.decode(o, skip_special_tokens=True).strip()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                looped = bool(lines) and collections.Counter(lines[-30:]).most_common(1)[0][1] >= 6
                fout.write(json.dumps({"id": g["id"], "page": g["page"], "kind": g["kind"],
                                       "content": text, "n_tokens": n,
                                       "truncated": n >= args.max_new_tokens,
                                       "looped": looped}, ensure_ascii=False) + "\n")
            fout.flush()
            ep.log(f"  batch {time.time() - tb:.0f}s; total {(time.time() - t0) / 60:.1f} min")
    ep.log(f"Shard {args.shard} finished -> {out_path}")


# ---------------------------------------------------------------- merge (CPU)
def load_results(prefix):
    rs = []
    for fn in sorted(glob.glob(os.path.join(OUT, f"{prefix}*.jsonl"))):
        for line in open(fn):
            try:
                rs.append(json.loads(line))
            except Exception:
                pass
    return rs


def gap_results():
    """Pass-1 answers, with pass-2 (window) answers replacing them where present."""
    res = {r["id"]: r for r in load_results("gaps_shard")}
    for r in load_results("gapswin_shard"):
        m = re.match(r"\s*PAGE:\s*(\d+)\s*\n", r["content"])
        if m:
            r["page"], r["content"] = int(m.group(1)), r["content"][m.end():]
        res[r["id"]] = r
    return res


def usable(g, r):
    norm = lambda t: re.sub(r"[\W_]+", "", t)
    return not (not r or r["looped"] or r["truncated"] or not r["content"].strip()
                or "[NOT FOUND]" in r["content"] or not g.get("confident", True)
                or KHMER.search(r["content"])                  # model can't read Khmer
                or norm(r["content"]) in norm(g["orig"]))      # just echoed the OCR


def figure_targets():
    """Unfilled image/formula gaps with a figure/algorithm/table caption next to them."""
    res = gap_results()
    return [g for g in json.load(open(GAPS))
            if g["kind"] in ("image", "formula") and not usable(g, res.get(g["id"]))
            and CAPTION.search(g["before"][-200:] + " " + g["after"][:200])]


def figure_pages(targets, radius=2):
    return sorted({q for g in targets for q in range(g["page"] - radius, g["page"] + radius + 1)
                   if 1 <= q <= 474})


def parse_figures(rec):
    """Split one page's pass-3 output into [{page, title, body}]."""
    if rec["looped"] or rec["truncated"] or "NO FIGURE" in rec["content"][:40]:
        return []
    figs = []
    for chunk in re.split(r"(?m)^\s*\**FIGURE:\**\s*", rec["content"])[1:]:
        title, _, body = chunk.partition("\n")
        body = re.sub(r"^```\w*\n|\n```$", "", body.strip())
        if all(re.sub(r"^[-*\s]+", "", l).startswith("[Image:") for l in body.split("\n") if l.strip()):
            continue  # only "[Image: ...]" descriptions (decoration, ECG strips): nothing worth adding
        if len(set(re.findall(r"[a-z]{4,}", body.lower()))) >= 8:  # drops ECG-machine settings etc.
            figs.append({"page": rec["page"], "title": title.strip().strip('"*'), "body": body})
    return figs


def assign_figures(targets, md):
    """Pick, per target gap, the best figure from nearby pages.
    title score = share of the figure title's words found next to the gap;
    novelty     = share of the figure's words NOT already in the OCR text around the gap
                  (Docling often did read the text boxes; then there's nothing to add)."""
    generic = {"untitled", "figure", "fig", "graphic", "schema", "the", "and", "for", "with"}
    words = lambda t: set(re.findall(r"[a-z]{3,}", t.lower())) - generic
    # "Figure 3", "Fig. 2", "Algorithm 1", "Figure (4)", "Schema 4" -> label numbers
    labels = lambda t: set(re.findall(r"(?:fig(?:ure)?|algorithm|graphic|schema|table)\.?\s*\(?(\d+)", t, re.I))
    algo = re.compile(r"algorithm|management|treatment", re.I)
    figs = [f for r in load_results("figpages_shard") for f in parse_figures(r)]
    used, out, report = set(), {}, []
    for g in targets:
        ctx_txt = g["before"][-300:] + " " + g["after"][:300]
        ctx, ctx_lab = words(ctx_txt), labels(ctx_txt)
        near = words(" ".join(md[max(0, g["start"] - 80):g["end"] + 80]))
        best = None
        for k, f in enumerate(figs):
            dist = abs(f["page"] - g["page"])
            if dist > 2 or k in used:
                continue
            if labels(f["title"]) and ctx_lab and not labels(f["title"]) & ctx_lab:
                continue  # e.g. gap wants Figure 1, this is Figure 3
            tw, bw = words(f["title"]), words(f["body"])
            title = len(tw & ctx) / len(tw) if tw else 0.0
            novelty = len(bw - near) / len(bw) if bw else 0.0
            score = (title, novelty >= 0.3, -dist)
            # weak title match: only for an "Algorithm"-type caption and an algorithm-type figure
            weak_ok = dist <= 1 and novelty >= 0.3 and algo.search(ctx_txt) and algo.search(f["title"])
            if novelty >= 0.15 and (title >= 0.6 or weak_ok):
                if best is None or score > best[0]:
                    best = (score, k, f, novelty)
        rep = {"gap": g["id"], "gap_page": g["page"],
               "context": (g["before"][-120:] + " || " + g["after"][:120]).replace("\n", " ")}
        if best:
            (title, _, _), k, f, nov = best
            used.add(k)
            out[g["id"]] = f
            rep.update(fig_page=f["page"], fig_title=f["title"], title_score=round(title, 2),
                       novelty=round(nov, 2), preview=f["body"][:200])
        report.append(rep)
    json.dump(report, open(os.path.join(OUT, "figassign.json"), "w"), ensure_ascii=False, indent=1)
    return out


def merge():
    md = open(os.path.join(ROOT, "ocr/output.md")).read().split("\n")
    gaps = {g["id"]: g for g in json.load(open(GAPS))}
    res = gap_results()
    figs = assign_figures(figure_targets(), md) if load_results("figpages_shard") else {}
    bad, n_fig = [], 0
    for gid in sorted(gaps, key=lambda k: -gaps[k]["start"]):  # bottom-up keeps indices valid
        g, r = gaps[gid], res.get(gid)
        if usable(g, r):
            c = re.sub(r"^```\w*\n|\n```$", "", r["content"].strip())
            head = f"<!-- qwen3 fill: {g['kind']}, page {r['page']} -->"
        elif gid in figs:
            f, n_fig = figs[gid], n_fig + 1
            c = (f"**{f['title']}**\n\n" if f["title"].lower() != "untitled" else "") + f["body"]
            head = f"<!-- qwen3 fill: {g['kind']} (figure pass), page {f['page']} -->"
        else:
            bad.append(gid)
            continue
        md[g["start"]:g["end"] + 1] = [head, c, "<!-- /qwen3 fill -->"]
    path = os.path.join(OUT, "ocr_filled.md")
    open(path, "w").write("\n".join(md))
    print(f"{len(gaps) - len(bad)}/{len(gaps)} gaps filled ({n_fig} by the figure pass) -> {path}")
    print(f"left as-is ({len(bad)}; missing/looped/truncated/not found): {sorted(bad)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--model", default="/mnt/mahdipou/models/Qwen3-VL-8B-Instruct")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--window", action="store_true", help="retry NOT FOUND gaps on pages p-1..p+1")
    ap.add_argument("--figures", action="store_true",
                    help="pass 3: transcribe all figures on pages near captioned unfilled image gaps")
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--max-pixels", type=int, default=1700 * 2400)
    a = ap.parse_args()
    prep() if a.prep else merge() if a.merge else run(a)
