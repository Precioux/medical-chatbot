#!/usr/bin/env python
"""NLLB-1.3B vs small LLMs used as a translation agent, X -> English. Same test sets as nllb_full_benchmark.ipynb.

    # one GPU job (each LLM loaded once, then COMET), quick run on the first 200 FLORES sentences:
    bash ../config/submit_H.sh h200 xagent "/mnt/mahdipou/ml/translation_agent.py --n 200" 1 8
    # full run (reuses the translations already made):
    bash ../config/submit_H.sh h200 xagent "/mnt/mahdipou/ml/translation_agent.py --n 1012" 1 8
    # login node, scores/table/chart only from saved outputs + saved COMET scores:
    python translation_agent.py --n 1012 --report-only

Test sets: FLORES-200 devtest khm/lao/vie -> eng (first --n sentences), and the 200 real Khmer medical questions of
out/xling_part3_queries.jsonl (reference: the dataset's English question).
NLLB-1.3B is not re-run: its saved outputs (out/nllb_bench/) are scored again with the extra metrics.
Scores: sacrebleu corpus BLEU and chrF++ (word_order=2) as in the NLLB benchmark, COMET (Unbabel/wmt22-comet-da),
numbers kept (every digit run of the source in the output), loops / empty outputs, seconds per 100 sentences.
Outputs: out/translation_agent/<model>.<set>.jsonl, out/translation_agent_results.json, out/translation_agent_report.md,
out/translation_agent_bleu.png
"""
import argparse, collections, json, os, re, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
TR = os.path.join(OUT, "translation_agent")
FL = os.path.join(ROOT, "data", "flores200", "flores200_dataset", "devtest")
MODELS_DIR = os.path.normpath(os.path.join(ROOT, "..", "models"))
COMET_LIB = os.path.normpath(os.path.join(ROOT, "..", "pylibs", "comet"))     # unbabel-comet, installed --no-deps

LANGS = {"khm": ("Khmer", "khm_Khmr"), "lao": ("Lao", "lao_Laoo"), "vie": ("Vietnamese", "vie_Latn")}
SETS = ["flores_khm", "flores_lao", "flores_vie", "medical_khm"]
SET_LABEL = {"flores_khm": "Khmer (FLORES)", "flores_lao": "Lao (FLORES)", "flores_vie": "Vietnamese (FLORES)",
             "medical_khm": "Khmer medical Qs"}
SET_LANG = {"flores_khm": "Khmer", "flores_lao": "Lao", "flores_vie": "Vietnamese", "medical_khm": "Khmer"}
LLMS = {  # name -> (path, loader)
    "Llama-2-7B-chat": (f"{MODELS_DIR}/Llama-2-7b-chat-hf", "causal"),
    "Llama-3.1-8B-Instruct (extra)": (f"{MODELS_DIR}/Llama-3.1-8B-Instruct", "causal"),
    "Gemma-3-4B-it": (f"{MODELS_DIR}/gemma-3-4b", "vlm"),
    "Qwen3-VL-8B (text-only)": (f"{MODELS_DIR}/Qwen3-VL-8B-Instruct", "vlm"),
}
NLLB = "NLLB-1.3B"
SYSTEM = ("You are a medical translator. Translate the user's text from {lang} into English. Output only the English "
          "translation, nothing else. Keep every number, unit, range and symbol exactly as written. Never drop a "
          "negation (not, no, never, avoid). Keep drug names as they are.")
DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩໐໑໒໓໔໕໖໗໘໙", "01234567890123456789")


def slug(m):
    return re.sub(r"[^A-Za-z0-9.]+", "_", m).strip("_")


# ---------------------------------------------------------------- data
def load_sets(n):
    eng = open(f"{FL}/eng_Latn.devtest", encoding="utf-8").read().splitlines()
    data = {}
    for k, (_, code) in LANGS.items():
        src = open(f"{FL}/{code}.devtest", encoding="utf-8").read().splitlines()
        data[f"flores_{k}"] = {"src": src[:n], "ref": eng[:n]}
    q = [json.loads(l) for l in open(os.path.join(OUT, "xling_part3_queries.jsonl"), encoding="utf-8")]
    data["medical_khm"] = {"src": [r["question_km"] for r in q], "ref": [r["question_en"] for r in q]}
    return data


def nllb_outputs(n):
    out = {}
    for k in LANGS:
        out[f"flores_{k}"] = open(os.path.join(OUT, "nllb_bench", f"flores_{k}-eng_devtest.1.3B.txt"),
                                  encoding="utf-8").read().splitlines()[:n]
    out["medical_khm"] = [json.loads(l)["back_en"] for l in open(os.path.join(OUT, "nllb_bench", "t2_khm_real.1.3B.jsonl"))]
    return out


# ---------------------------------------------------------------- cleaning / checks
PREAMBLE = re.compile(r"^\s*(?:(?:sure|okay|ok|certainly|of course)[,!.]?\s*)?(?:here(?:'s| is| are)\b[^:\n]*:|"
                      r"(?:the\s+)?(?:english\s+)?translation(?:\s+in\s+english)?\s*(?:is)?\s*:|english\s*:)\s*", re.I)
NOTE = re.compile(r"^\s*[\(*_]*\s*(?:note|notes|explanation|translation note|i translated|i kept|please note)\b", re.I)


SCRIPT = re.compile(r"[\u1780-\u17ff\u0e80-\u0eff]")


def clean(raw):
    """Keep only the translation: drop <think>, preamble paragraphs ('Sure, here is ...:'), trailing notes, echoed
    Khmer/Lao source, wrapping quotes and bold markers. Multi-paragraph translations (answer options) are kept."""
    t = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S).strip()
    t = re.sub(r"\*\*|__", "", t)
    paras = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    # leading preamble paragraphs: end with ':' and say translate/translation, or match PREAMBLE entirely
    while len(paras) > 1 and (re.search(r"(translat|here is|here's)[^\n]*:\s*$", paras[0], re.I)
                              or not PREAMBLE.sub("", paras[0]).strip()):
        paras.pop(0)
    # echoed source: paragraphs that are mostly Khmer/Lao script
    eng = [p for p in paras if len(SCRIPT.findall(p)) < 0.3 * len(re.sub(r"\s", "", p))]
    if eng:                       # if nothing is English, keep the output: it is scored (and counted) as not English
        paras = eng
    # trailing notes (never the first paragraph)
    for k in range(1, len(paras)):
        if NOTE.match(paras[k]):
            paras = paras[:k]
            break
    if not paras:
        return ""
    paras[0] = re.sub(r"^\s*#+\s*", "", paras[0])
    paras[0] = PREAMBLE.sub("", paras[0], count=1).strip()
    t = "\n".join(re.sub(r"[ \t]*\n[ \t]*", "\n", p) for p in paras).strip()
    t = re.sub(r"\s*\((?:note|literally|lit\.)[^)]*\)\s*$", "", t, flags=re.I).strip()
    if len(t) >= 2 and t[0] in "\"'“‘«" and t[-1] in "\"'”’»" and t.count(t[0]) <= 2:
        t = t[1:-1].strip()
    return t


def digit_runs(s):
    return re.findall(r"\d+", (s or "").translate(DIGITS))


def not_english(t):
    """Output is mostly Khmer/Lao script: the model wrote in the source language instead of translating."""
    return len(SCRIPT.findall(t or "")) >= 0.3 * max(1, len(re.sub(r"\s", "", t or "")))


def numbers_kept(src, hyp):
    need, have = collections.Counter(digit_runs(src)), collections.Counter(digit_runs(hyp))
    kept = sum(min(c, have[d]) for d, c in need.items())
    return kept, sum(need.values())


def looped(t):
    w = (t or "").split()
    grams = collections.Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
    return bool(grams) and grams.most_common(1)[0][1] >= 4


# ---------------------------------------------------------------- generation
def load_llm(path, kind):
    import torch
    from transformers import AutoModelForCausalLM, AutoModelForImageTextToText, AutoProcessor, AutoTokenizer
    if kind == "causal":
        tok = AutoTokenizer.from_pretrained(path)
        model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map="cuda").eval()
        proc = None
    else:
        proc = AutoProcessor.from_pretrained(path)
        tok = proc.tokenizer
        model = AutoModelForImageTextToText.from_pretrained(path, dtype=torch.bfloat16, device_map="cuda").eval()
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.unk_token or tok.eos_token
    return model, tok, proc


def prompts(texts, lang, tok, proc):
    out = []
    for t in texts:
        if proc is None:
            msgs = [{"role": "system", "content": SYSTEM.format(lang=lang)}, {"role": "user", "content": t}]
            out.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        else:
            msgs = [{"role": "system", "content": [{"type": "text", "text": SYSTEM.format(lang=lang)}]},
                    {"role": "user", "content": [{"type": "text", "text": t}]}]
            out.append(proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    return out


def translate(model, tok, proc, texts, lang, max_new, bs, log):
    import torch
    ps = prompts(texts, lang, tok, proc)
    order = sorted(range(len(ps)), key=lambda i: -len(tok(ps[i], add_special_tokens=False)["input_ids"]))
    res = [None] * len(ps)
    gen_cfg = dict(do_sample=False, temperature=None, top_p=None, top_k=None, max_new_tokens=max_new,
                   pad_token_id=tok.pad_token_id)
    for s in range(0, len(order), bs):
        idx = order[s:s + bs]
        enc = tok([ps[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        with torch.no_grad():
            g = model.generate(**enc, **gen_cfg)
        new = g[:, enc["input_ids"].shape[1]:]
        for i, row in zip(idx, new):
            n_tok = int((row != tok.pad_token_id).sum())
            res[i] = {"raw": tok.decode(row, skip_special_tokens=True), "new_tokens": n_tok, "hit_max": n_tok >= max_new}
        log(f"    batch {s // bs + 1}/{(len(order) + bs - 1) // bs}")
    return res


def run_llms(data, n, bs, log):
    os.makedirs(TR, exist_ok=True)
    for name, (path, kind) in LLMS.items():
        todo = {}
        for st in SETS:
            f = os.path.join(TR, f"{slug(name)}.{st}.jsonl")
            have = {json.loads(l)["i"]: json.loads(l) for l in open(f)} if os.path.exists(f) else {}
            need = [i for i in range(len(data[st]["src"])) if i not in have]
            if need:
                todo[st] = (f, have, need)
        if not todo:
            log(f"{name}: all outputs present, skipped")
            continue
        t0 = time.time()
        model, tok, proc = load_llm(path, kind)
        log(f"{name}: loaded in {time.time() - t0:.0f} s; sets {[(k, len(v[2])) for k, v in todo.items()]}")
        for st, (f, have, need) in todo.items():
            src = [data[st]["src"][i] for i in need]
            t1 = time.time()
            out = translate(model, tok, proc, src, SET_LANG[st], 384 if st == "medical_khm" else 256, bs, lambda m: None)
            secs = time.time() - t1
            for i, o in zip(need, out):
                have[i] = {"i": i, **o, "clean": clean(o["raw"]), "sec_per_100": round(100 * secs / len(need), 2)}
            with open(f, "w", encoding="utf-8") as fh:
                for i in sorted(have):
                    fh.write(json.dumps(have[i], ensure_ascii=False) + "\n")
            log(f"  {st}: {len(need)} sentences in {secs:.0f} s ({100 * secs / len(need):.1f} s/100)")
        import torch, gc
        del model
        gc.collect(); torch.cuda.empty_cache()


# ---------------------------------------------------------------- scoring
def system_outputs(data, n):
    """{model: {set: {"hyp": [...], "meta": [...] or None}}}"""
    systems = {NLLB: {st: {"hyp": h, "meta": None} for st, h in nllb_outputs(n).items()}}
    for name in LLMS:
        systems[name] = {}
        for st in SETS:
            f = os.path.join(TR, f"{slug(name)}.{st}.jsonl")
            if not os.path.exists(f):
                continue
            rows = {json.loads(l)["i"]: json.loads(l) for l in open(f)}
            m = len(data[st]["src"])
            if all(i in rows for i in range(m)):
                for i in range(m):
                    rows[i]["clean"] = clean(rows[i]["raw"])
                systems[name][st] = {"hyp": [rows[i]["clean"] for i in range(m)], "meta": [rows[i] for i in range(m)]}
    return systems


def comet_scores(data, systems, n, log, gpu=True):
    """Sentence-level COMET per model/set; cached in out/translation_agent/comet.n<N>.json."""
    cache_f = os.path.join(TR, f"comet.n{n}.json")
    cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
    import hashlib
    hkey = lambda m, st: hashlib.sha1("\n".join(systems[m][st]["hyp"]).encode()).hexdigest()[:12]
    todo = [(m, st) for m, sets in systems.items() for st in sets
            if cache.get(f"{m}|{st}|hash") != hkey(m, st)]
    if todo and gpu:
        sys.path.insert(0, COMET_LIB)
        from comet import download_model, load_from_checkpoint
        cm = load_from_checkpoint(download_model("Unbabel/wmt22-comet-da"))
        for m, st in todo:
            d = data[st]
            batch = [{"src": s, "mt": h, "ref": r} for s, h, r in zip(d["src"], systems[m][st]["hyp"], d["ref"])]
            o = cm.predict(batch, batch_size=64, gpus=1, progress_bar=False)
            cache[f"{m}|{st}"] = [round(float(x), 4) for x in o.scores]
            cache[f"{m}|{st}|hash"] = hkey(m, st)
            log(f"  COMET {m} {st}: {sum(o.scores) / len(o.scores):.4f}")
            json.dump(cache, open(cache_f, "w"))
    elif todo:
        log(f"COMET missing or stale for {todo} (needs the GPU job)")
        for m, st in todo:
            cache.pop(f"{m}|{st}", None)
    return {k: v for k, v in cache.items() if not k.endswith("|hash")}


def score(data, systems, comet, n):
    import sacrebleu
    rows = []
    for m, sets in systems.items():
        for st, s in sets.items():
            d, hyp = data[st], s["hyp"]
            k = [numbers_kept(a, b) for a, b in zip(d["src"], hyp)]
            meta = s["meta"]
            c = comet.get(f"{m}|{st}")
            rows.append({
                "model": m, "set": st, "label": SET_LABEL[st], "n": len(hyp),
                "BLEU": round(sacrebleu.corpus_bleu(hyp, [d["ref"]]).score, 2),
                "chrF++": round(sacrebleu.corpus_chrf(hyp, [d["ref"]], word_order=2).score, 2),
                "COMET": round(sum(c) / len(c), 4) if c else None,
                "numbers_kept": sum(a for a, _ in k), "numbers_total": sum(b for _, b in k),
                "numbers_kept_pct": round(100 * sum(a for a, _ in k) / max(1, sum(b for _, b in k)), 1),
                "sentences_all_numbers_kept_pct": round(100 * sum(1 for a, b in k if a == b) / len(k), 1),
                "loops": sum(1 for i, h in enumerate(hyp) if looped(h) or (meta and meta[i]["hit_max"])),
                "hit_max_tokens": sum(1 for x in meta if x["hit_max"]) if meta else None,
                "empty": sum(1 for h in hyp if not h.strip()),
                "not_english": sum(1 for h in hyp if h.strip() and not_english(h)),
                "cleaned": sum(1 for x in meta if x["clean"].strip() != x["raw"].strip()) if meta else None,
                "sec_per_100": meta[0]["sec_per_100"] if meta else None,
            })
    ref_numbers = {}
    for st, d in data.items():                     # how often the human reference itself keeps the digits
        k = [numbers_kept(a, b) for a, b in zip(d["src"], d["ref"])]
        ref_numbers[st] = round(100 * sum(a for a, _ in k) / max(1, sum(b for _, b in k)), 1)
    return rows, ref_numbers


def disagreements(data, systems, comet, k=5):
    out = {}
    for st in SETS:
        ms = [m for m in systems if st in systems[m] and f"{m}|{st}" in comet]
        if len(ms) < 2:
            continue
        spread = []
        for i in range(len(data[st]["src"])):
            v = [comet[f"{m}|{st}"][i] for m in ms]
            spread.append((max(v) - min(v), i))
        out[st] = [{"i": i, "comet_spread": round(sp, 3), "source": data[st]["src"][i], "reference": data[st]["ref"][i],
                    "outputs": {m: {"text": systems[m][st]["hyp"][i], "COMET": comet[f"{m}|{st}"][i]} for m in ms}}
                   for sp, i in sorted(spread, reverse=True)[:k]]
    return out


# ---------------------------------------------------------------- report
def chart(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    models = [NLLB] + list(LLMS)
    colors = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac"]      # categorical slots 1-5, fixed order
    sets = [s for s in SETS if any(r["set"] == s for r in rows)]
    w = 0.8 / len(models)
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    for j, m in enumerate(models):
        vals = [next((r["BLEU"] for r in rows if r["model"] == m and r["set"] == s), 0) for s in sets]
        xs = [i + (j - (len(models) - 1) / 2) * w for i in range(len(sets))]
        bars = ax.bar(xs, vals, w * 0.92, color=colors[j], label=m, zorder=2)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f}", ha="center", va="bottom", fontsize=7, color="#444")
    ax.set_xticks(range(len(sets)))
    ax.set_xticklabels([SET_LABEL[s] for s in sets])
    ax.set_ylabel("BLEU (sacrebleu, corpus)")
    n = next(r["n"] for r in rows if r["set"] == "flores_khm")
    ax.set_title(f"X → English BLEU: NLLB-1.3B vs LLM translation agents (FLORES devtest first {n}, 200 Khmer medical Qs)",
                 fontsize=10, loc="left")
    ax.grid(axis="y", color="#e5e5e5", zorder=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#bbb"); ax.spines["bottom"].set_color("#bbb")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    ax.set_ylim(0, max(r["BLEU"] for r in rows) * 1.2 + 2)
    fig.tight_layout()
    fig.savefig(path)


def report(rows, ref_numbers, ex, n, path):
    L = [f"# Translation agent benchmark (X → English), FLORES devtest first {n} + 200 Khmer medical questions", "",
         "BLEU / chrF++: sacrebleu corpus scores, same settings as the NLLB benchmark. COMET: Unbabel/wmt22-comet-da. "
         "Numbers kept: digit runs of the source found in the output. Loops: repeated 3-gram ≥ 4 times or output "
         "hit the token limit. Not English: output mostly in Khmer/Lao script (the model rewrote instead of translating). NLLB-1.3B: saved outputs of the earlier benchmark (beam 4, sentence by sentence), "
         "not re-run, so no speed figure.", "",
         "| model | set | BLEU | chrF++ | COMET | numbers kept | loops | empty | not English | s / 100 sent. |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for st in SETS:
        for r in [r for r in rows if r["set"] == st]:
            L.append(f"| {r['model']} | {r['label']} | {r['BLEU']:.1f} | {r['chrF++']:.1f} | "
                     f"{r['COMET'] if r['COMET'] is not None else '-'} | {r['numbers_kept_pct']}% "
                     f"({r['numbers_kept']}/{r['numbers_total']}) | {r['loops']} | {r['empty']} | {r['not_english']} | "
                     f"{r['sec_per_100'] if r['sec_per_100'] is not None else 'n/a'} |")
    L += ["", "Numbers kept by the human English reference itself (FLORES sometimes writes numbers as words): "
          + ", ".join(f"{SET_LABEL[k]} {v}%" for k, v in ref_numbers.items()), ""]
    for st, xs in ex.items():
        L += [f"## Largest disagreements: {SET_LABEL[st]}", ""]
        for x in xs:
            L += [f"**#{x['i']}** (COMET spread {x['comet_spread']})", "", f"- source: {x['source']}",
                  f"- reference: {x['reference']}"]
            L += [f"- {m} ({o['COMET']:.3f}): {o['text']}" for m, o in x["outputs"].items()]
            L.append("")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="FLORES sentences per language (200 quick, 1012 all)")
    ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("HF_HOME", os.path.normpath(os.path.join(ROOT, "..", "hf_cache")))
    os.makedirs(TR, exist_ok=True)
    log = lambda m: print(time.strftime("%H:%M:%S"), m, flush=True)
    data = load_sets(a.n)
    if not a.report_only:
        run_llms(data, a.n, a.bs, log)
    systems = system_outputs(data, a.n)
    comet = comet_scores(data, systems, a.n, log, gpu=not a.report_only)
    rows, ref_numbers = score(data, systems, comet, a.n)
    ex = disagreements(data, systems, comet)
    json.dump({"config": {"n_flores": a.n, "system_prompt": SYSTEM, "decoding": "greedy (temperature 0)",
                          "models": {NLLB: "facebook/nllb-200-1.3B (saved outputs, beam 4)",
                                     **{m: p for m, (p, _) in LLMS.items()}},
                          "comet": "Unbabel/wmt22-comet-da", "bleu": "sacrebleu corpus_bleu default",
                          "chrf": "sacrebleu corpus_chrf word_order=2"},
               "scores": rows, "reference_numbers_kept_pct": ref_numbers, "examples": ex,
               "comet_sentence_scores": comet},
              open(os.path.join(OUT, "translation_agent_results.json"), "w"), indent=1, ensure_ascii=False)
    chart(rows, os.path.join(OUT, "translation_agent_bleu.png"))
    report(rows, ref_numbers, ex, a.n, os.path.join(OUT, "translation_agent_report.md"))
    log("wrote out/translation_agent_results.json, out/translation_agent_report.md, out/translation_agent_bleu.png")


if __name__ == "__main__":
    main()
