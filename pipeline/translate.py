"""Stage 1: find non-English text (Khmer / Lao by Unicode block, Vietnamese by its letters) and translate it to
English with NLLB-200 1.3B, using the fixed pipeline from mt_safety_test.py:
  dash normalisation -> sentence split (+ windows for long sentences) -> beam search -> loop retry with an
  n-gram block -> decimal repair -> number words to digits -> number guard (a translation that lost a number is
  retried with 8 beams) -> back-translation to the source language, chrF against the source = quality estimate
  (qe_chrf). Stage 2 decides from qe_chrf whether a translation is used (config extract.mt_min_chrf).
Khmer/Lao digits are mapped to ASCII before translation so numbers survive.

Sources: the PDF text layer (lines decoded like build_unified does); pages without one: Chandra's output, plus the
Chandra algorithm blocks on those pages. A segment is a maximal run of the script inside one line (English words
and ASCII numbers around it are left alone); a Vietnamese line is translated whole.

Outputs (stage1_translate/): translations.jsonl (one row per unique segment per page), report.json
"""
import collections, json, os, re, time

from pipeline.common import (DIGITS, StageFailed, inp, read_jsonl, script_runs_re, seg_key, stage_dir,
                             vietnamese_line, write_json, write_jsonl)


# ---------------------------------------------------------------- segment discovery
def page_sources(cfg):
    """{page: [(layer, line)]} for every page: text-layer lines, or Chandra lines on pages without a layer."""
    import pymupdf
    import build_unified as BU
    import merge_sources as M
    pdf = pymupdf.open(inp(cfg, "pdf"))
    chandra = {r["page"]: r["content"] for r in read_jsonl(inp(cfg, "chandra_pages"))}
    algos = collections.defaultdict(list)
    for b in read_jsonl(inp(cfg, "mmore_build")):
        if b["type"] == "algorithm":
            algos[b["page"]].append(b["content"])
    no_layer = set(cfg["translate"]["no_text_layer_pages"])
    out = {}
    for pno in range(1, pdf.page_count + 1):
        page = pdf[pno - 1]
        if pno in no_layer and len(re.sub(r"\s|\d", "", page.get_text())) < 5:
            lines = [("chandra", l) for blk in M.split_text(M.html_to_text(chandra.get(pno, "")))
                     for l in blk.splitlines()]
            lines += [("chandra_algorithm", l) for a in algos.get(pno, []) for l in a.splitlines()]
        else:
            lines = [("pdf_text", ln[2]) for ln in BU.page_lines(page)]
        out[pno] = lines
    return out


def find_segments(cfg, sources):
    runs = script_runs_re(cfg)
    segs, vi_rejected = collections.OrderedDict(), []
    for pno, lines in sources.items():
        for layer, line in lines:
            for lang, rx in runs.items():
                for m in rx.finditer(line):
                    k = (pno, seg_key(m.group(0)))
                    if k not in segs:
                        segs[k] = {"page": pno, "lang": lang, "layer": layer, "original": m.group(0).strip(),
                                   "key": k[1], "occurrences": 0}
                    segs[k]["occurrences"] += 1
            is_vi, n = vietnamese_line(cfg, line)
            if is_vi:
                k = (pno, seg_key(line))
                segs.setdefault(k, {"page": pno, "lang": "vie", "layer": layer, "original": line.strip(),
                                    "key": k[1], "occurrences": 0})["occurrences"] += 1
            elif n:
                vi_rejected.append({"page": pno, "layer": layer, "line": line[:200], "vi_words": n})
    return list(segs.values()), vi_rejected


# ---------------------------------------------------------------- translation
def split_source(text, tok, max_tokens):
    """Sentence split for Khmer/Lao/Vietnamese source: at ។ ៕ . ! ? and line breaks; then cut sentences that are
    longer than max_tokens into windows at spaces (Khmer separates phrases with spaces)."""
    parts = [x.strip() for x in re.split(r"(?<=[។៕!?])\s*|(?<=\.)\s+|\n+", text) if x and x.strip()]
    out = []
    for s in parts:
        if len(tok(s, add_special_tokens=False)["input_ids"]) <= max_tokens:
            out.append(s)
            continue
        cur = ""
        for w in s.split(" "):
            cand = f"{cur} {w}".strip()
            if cur and len(tok(cand, add_special_tokens=False)["input_ids"]) > max_tokens:
                out.append(cur)
                cur = w
            else:
                cur = cand
        if cur:
            out.append(cur)
    return out


def nums(s):
    """Numbers as values: '04' == '4', Khmer/Lao digits as ASCII."""
    return [re.sub(r"^0+(?=\d)", "", n) for n in re.findall(r"\d+(?:\.\d+)?", s.translate(DIGITS))]


NUM_WORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
NUM_WORDS.update({w: str(i) for i, w in enumerate("zeroth first second third fourth fifth sixth seventh eighth ninth tenth".split())})


def repair_number_words(src, tgt):
    """NLLB writes small numbers as words ('ភាគ ១' -> 'Part One'): put back the digit the source had."""
    for n in [n for n in nums(src) if n not in nums(tgt)]:
        for w, v in NUM_WORDS.items():
            if v == n and re.search(rf"\b{w}\b", tgt, re.I):
                tgt = re.sub(rf"\b{w}\b", n, tgt, count=1, flags=re.I)
                break
    return tgt


def looped_text(t):
    w = t.split() if " " in t else list(t)
    grams = collections.Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
    return bool(grams) and grams.most_common(1)[0][1] >= 5


def translate_segments(cfg, segs):
    # import transformers before touching torch.cuda: the other order fails in the runai container
    # (torch._dynamo ImportError, NP_SUPPORTED_MODULES; senv has mixed torch 2.6/2.8 files)
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    from mt_safety_test import normalize_en, repair_decimals
    tc = cfg["translate"]
    dev = tc["device"]
    if dev.startswith("cuda") and not torch.cuda.is_available():
        if not tc.get("allow_cpu"):
            raise StageFailed("stage 1 needs a GPU (CLAUDE.md: no model code on the login node). Run it on runai:\n"
                              "  bash ../config/submit_H.sh h200 pipeline-translate "
                              "\"/mnt/mahdipou/ml/run_pipeline.py --to translate\" 1 8\n"
                              "or set translate.allow_cpu: true in config.yaml.")
        dev = "cpu"
    tok = AutoTokenizer.from_pretrained(tc["model"])
    model = AutoModelForSeq2SeqLM.from_pretrained(
        tc["model"], torch_dtype=torch.float16 if dev.startswith("cuda") else torch.float32).to(dev).eval()
    langs = {**{k: v["nllb"] for k, v in tc["scripts"].items()}, "vie": tc["vietnamese"]["nllb"]}
    stats = collections.Counter()

    @torch.no_grad()
    def gen(texts, src, beams, no_repeat=0):
        tok.src_lang = src
        out = []
        for s in range(0, len(texts), tc["batch_size"]):
            batch = texts[s:s + tc["batch_size"]]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=256).to(dev)
            g = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(tc["target"]), num_beams=beams,
                               no_repeat_ngram_size=no_repeat, max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
            out += [t.strip() for t in tok.batch_decode(g, skip_special_tokens=True)]
        return out

    @torch.no_grad()
    def gen_to(texts, tgt_code):
        """English -> tgt_code (back-translation)."""
        tok.src_lang = tc["target"]
        out = []
        for s in range(0, len(texts), tc["batch_size"]):
            enc = tok(texts[s:s + tc["batch_size"]], return_tensors="pt", padding=True, truncation=True, max_length=256).to(dev)
            g = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(tgt_code), num_beams=tc["num_beams"],
                               max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
            out += [t.strip() for t in tok.batch_decode(g, skip_special_tokens=True)]
        return out

    for lang in sorted({s["lang"] for s in segs}):
        group = [s for s in segs if s["lang"] == lang]
        for s in group:
            s["input"] = normalize_en(s["original"].translate(DIGITS))
            s["sentences_in"] = split_source(s["input"], tok, tc["max_input_tokens"])
        flat = [x for s in group for x in s["sentences_in"]]
        uniq = list(dict.fromkeys(flat))                        # Chandra repeats lines: translate each once
        res = dict(zip(uniq, gen(uniq, langs[lang], tc["num_beams"])))
        for src, t in list(res.items()):
            if looped_text(t) and not looped_text(src):         # runaway generation: retry with an n-gram block
                res[src] = gen([src], langs[lang], tc["num_beams"], no_repeat=3)[0]
                stats["loop_retry"] += 1
            res[src] = repair_number_words(src, repair_decimals(src, res[src]))
            miss = [n for n in nums(src) if n not in nums(res[src])]
            if miss:                                            # number guard
                t2 = repair_number_words(src, repair_decimals(src, gen([src], langs[lang], 8)[0]))
                stats["number_retry"] += 1
                if len([n for n in nums(src) if n not in nums(t2)]) < len(miss):
                    res[src] = t2
        # quality estimate: back-translate English -> source language, chrF against the source
        import sacrebleu
        outs = list(dict.fromkeys(res.values()))
        tok.src_lang = tc["target"]
        back = {}
        for t, bt in zip(outs, gen_to(outs, langs[lang])):
            back[t] = bt
        for s in group:
            s["sentences_out"] = [res[x] for x in s["sentences_in"]]
            s["translation"] = " ".join(s["sentences_out"])
            s["back_translation"] = " ".join(back[res[x]] for x in s["sentences_in"])
            s["qe_chrf"] = round(sacrebleu.sentence_chrf(s["back_translation"], [s["input"]]).score, 1)
            flags = {}
            lost = [n for n in nums(s["input"]) if n not in nums(s["translation"])]
            if lost:
                flags["numbers_lost"] = lost
            if looped_text(s["input"]):
                flags["source_repetitive"] = True             # e.g. Chandra hallucinated loops on scanned pages
            s["flags"] = flags
        stats[f"segments_{lang}"] += len(group)
        stats[f"sentences_{lang}"] += len(uniq)
        print(f"[translate] {lang}: {len(group)} segments, {len(uniq)} unique sentences", flush=True)
    return dict(stats)


def translate_in_subprocess(cfg, segs, out, log):
    """NLLB runs in a fresh interpreter that never imports pymupdf: with pymupdf loaded first, importing
    transformers fails in the runai container (torch._dynamo ImportError 'NP_SUPPORTED_MODULES')."""
    import subprocess, sys
    from pipeline.common import ROOT
    job = os.path.join(out, "_nllb_job.json")
    write_json(job, {"cfg": cfg, "segments": segs})
    r = subprocess.run([sys.executable, "-u", "-m", "pipeline.translate", job], cwd=ROOT)
    if r.returncode != 0:
        raise StageFailed(f"NLLB worker exited with {r.returncode}")
    res = json.load(open(job))
    segs[:] = res["segments"]
    os.remove(job)
    return res["stats"]


def run(cfg, log):
    out = stage_dir(cfg, "translate")
    t0 = time.time()
    sources = page_sources(cfg)
    segs, vi_rejected = find_segments(cfg, sources)
    log(f"found {len(segs)} non-English segments on pages {sorted({s['page'] for s in segs})}")
    stats = translate_in_subprocess(cfg, segs, out, log) if segs else {}
    for i, s in enumerate(segs):
        s["seg_id"] = f"seg_{i:04d}"
        s["source_numbers"] = nums(s["input"])
    order = ["seg_id", "page", "lang", "layer", "key", "original", "input", "sentences_in", "sentences_out",
             "translation", "back_translation", "qe_chrf", "source_numbers", "occurrences", "flags"]
    write_jsonl(os.path.join(out, "translations.jsonl"), [{k: s.get(k) for k in order} for s in segs])
    per_page = collections.defaultdict(lambda: collections.Counter())
    for s in segs:
        per_page[s["page"]][f"{s['lang']}/{s['layer']}"] += 1
    report = {"model": cfg["translate"]["model"],
              "pages_translated": sorted(per_page),
              "segments_per_page": {str(k): dict(v) for k, v in sorted(per_page.items())},
              "segments_total": len(segs), "stats": stats,
              "segments_with_numbers_lost": [(s["seg_id"], s["page"], s["flags"]["numbers_lost"]) for s in segs
                                             if s["flags"].get("numbers_lost")],
              "segments_with_repetitive_source": [s["seg_id"] for s in segs if s["flags"].get("source_repetitive")],
              "vietnamese_candidates_rejected": vi_rejected,
              "seconds": round(time.time() - t0, 1)}
    write_json(os.path.join(out, "report.json"), report)
    log(f"translated {len(segs)} segments; pages {report['pages_translated']}")
    return report


if __name__ == "__main__":                                   # worker: python -m pipeline.translate <job.json>
    import sys
    _job = json.load(open(sys.argv[1]))
    os.environ.setdefault("HF_HOME", _job["cfg"]["hf_home"] if os.path.isabs(_job["cfg"]["hf_home"]) else
                          os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _job["cfg"]["hf_home"]))
    os.environ.setdefault("USE_TF", "0"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
    _job["stats"] = translate_segments(_job["cfg"], _job["segments"])
    write_json(sys.argv[1], _job)
