#!/usr/bin/env python
"""English -> Khmer / Lao / Vietnamese on 100 random guideline chunks: NLLB-1.3B vs Qwen3-VL-8B vs SEA-LION v4 (27B, and the small 4B-VL / Apertus-8B models).

    # GPU job: select chunks, translate with the three systems, back-translate, COMET, report (resumable)
    bash ../config/submit_H.sh h200 revmt "/mnt/mahdipou/ml/reverse_translation.py" 1 8
    # login node: report/chart only from saved outputs + saved COMET scores
    python reverse_translation.py --report-only

There is no human Khmer/Lao/Vietnamese reference for the guideline, so quality is measured two ways:
  1. checks on the translation itself (mt_safety_test.py checks): numbers (locale-aware), negation cue present,
     drug names kept (Latin, or recovered in back-translation), units, right script, loops / empty output.
  2. round trip: every translation is back-translated to English by NLLB-1.3B AND by SEA-LION (two independent
     back-translators, so no system is judged only by itself) and compared with the English source
     (chrF++, COMET wmt22-comet-da with src = translation, mt = back-translation, ref = English chunk).
NLLB uses the fixed mt_safety pipeline (sentence by sentence, table cells one by one, decimals repaired).
The LLMs translate the whole chunk in one prompt (greedy).
Chunks: out/pipeline/stage4_chunk/chunks_256.jsonl, body text + tables + flowcharts <= 384 tokens, author lists
and Qwen3 image descriptions left out, 100 drawn with seed 0.
Outputs: out/reverse_mt/ (chunks.jsonl, fwd/, bt/, comet.json), out/reverse_mt_report.md,
out/reverse_mt_results.json, out/reverse_mt.png
"""
import argparse, collections, hashlib, json, os, random, re, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import translation_agent as TA                                                    # noqa: E402  (no heavy imports)
from mt_safety_test import (DRUG_RE, EN_NEG, TGT_NEG, drug_found, multiset_hits, normalize_en, numbers,  # noqa: E402
                            repair_decimals, split_en, units)

OUT = os.path.join(ROOT, "out")
D = os.path.join(OUT, "reverse_mt")
CHUNKS_IN = os.path.join(OUT, "pipeline", "stage4_chunk", "chunks_256.jsonl")
NLLB_ID = "facebook/nllb-200-1.3B"
LANGS = {"khm": ("Khmer", "khm_Khmr"), "lao": ("Lao", "lao_Laoo"), "vie": ("Vietnamese", "vie_Latn")}
NLLB = "NLLB-1.3B"
NLLB33 = "NLLB-3.3B"
# other NLLB sizes: forward only, same fixed pipeline as NLLB-1.3B (back-translation stays NLLB-1.3B + SEA-LION)
NLLB_FWD_EXTRA = {NLLB33: "facebook/nllb-200-3.3B"}
QWEN = "Qwen3-VL-8B"
SEAL = "SEA-LION-v4-27B-IT"
QSL4, GSL4, APSL = "Qwen-SEA-LION-v4-4B-VL", "Gemma-SEA-LION-v4-4B-VL", "Apertus-SEA-LION-v4-8B-IT"
# Qwen-SEA-LION-4B and Apertus-SEA-LION-8B were dropped (2026-11-27): Qwen-SEA-LION-4B looped on most Khmer/Lao chunks,
# Apertus was too slow (17 s/chunk Khmer). Their forward outputs stay in out/reverse_mt/fwd/; they are not scored or back-translated.
S2_3, S2_8, S2_20 = "Sailor2-3B-Chat", "Sailor2-8B-Chat", "Sailor2-20B-Chat"
# Gemma-SEA-LION-4B dropped too; Sailor2-3B/8B weights deleted before this test ran (2026-11-27)
SYSTEMS = [NLLB, NLLB33, QWEN, SEAL, S2_20]
# no longer run, but their saved forward outputs are still scored in the report (no back-translation / COMET)
REPORT_ONLY = [QSL4, GSL4, APSL]
# name -> (path, loader) from translation_agent.LLMS; SEA-LION-27B must be the last LLM (it back-translates all of them)
LLM_PATH = {QWEN: TA.LLMS["Qwen3-VL-8B (text-only)"], QSL4: TA.LLMS[QSL4], GSL4: TA.LLMS[GSL4], APSL: TA.LLMS[APSL],
            S2_3: TA.LLMS[S2_3], S2_8: TA.LLMS[S2_8], S2_20: TA.LLMS[S2_20], SEAL: TA.LLMS["SEA-LION-v4-27B-IT"]}
BACK = [NLLB, SEAL]                                     # back-translators
FWD_SYSTEM = ("You are a medical translator. Translate the user's text from English into {lang}. Output only the "
              "{lang} translation, nothing else. Keep every number, unit, range and symbol exactly as written. Never "
              "drop a negation (not, no, never, avoid). Keep drug names and abbreviations in their original Latin "
              "spelling. Keep the markdown layout (headings, list markers, table pipes).")
SCRIPT_RE = {"khm": re.compile(r"[ក-៿]"), "lao": re.compile(r"[຀-໿]")}
VI_MARKS = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)


def log(m):
    print(time.strftime("%H:%M:%S"), m, flush=True)


def slug(m):
    return re.sub(r"[^A-Za-z0-9.]+", "_", m).strip("_")


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def write_jsonl(p, rows):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- chunks
def select(n=100, seed=0):
    p = os.path.join(D, "chunks.jsonl")
    if os.path.exists(p):
        return read_jsonl(p)
    pool = [r for r in read_jsonl(CHUNKS_IN)
            if r["source_type"] in ("body_text", "table", "flowchart") and r["source"] != "qwen3"
            and r["tokens"] <= 384 and r["text_en"].count("Dr.") < 4 and len(r["text_en"].split()) >= 15]
    rows = random.Random(seed).sample(pool, n)
    rows = [{"id": i, "chunk_id": r["chunk_id"], "source_type": r["source_type"], "citation": r["citation"],
             "tokens": r["tokens"], "text": r["text_en"]} for i, r in enumerate(rows)]
    write_jsonl(p, rows)
    log(f"selected {n} of {len(pool)} candidate chunks -> {p} {dict(collections.Counter(r['source_type'] for r in rows))}")
    return rows


# ---------------------------------------------------------------- layout-preserving segmentation (for NLLB)
TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
PREFIX = re.compile(r"^(\s*(?:#+|[-*•☐]|\(?\d+[.)]|[a-z][.)])\s+)")


def segment(text, splitter):
    """Split into a template of literal pieces and pieces to translate, line by line: table cells are translated
    one by one, heading / list prefixes are kept, the rest is split into sentences by `splitter`."""
    tmpl = []
    for li, line in enumerate(text.split("\n")):
        if li:
            tmpl.append(("lit", "\n"))
        if not line.strip() or (TABLE_SEP.match(line) and "-" in line):
            tmpl.append(("lit", line)); continue
        if line.lstrip().startswith("|"):
            cells = line.split("|")
            for ci, c in enumerate(cells):
                if ci:
                    tmpl.append(("lit", "|"))
                if re.search(r"[^\W\d_]", c):
                    lead, core, trail = re.match(r"^(\s*)(.*?)(\s*)$", c).groups()
                    tmpl += [("lit", lead), ("tr", core), ("lit", trail)]
                else:
                    tmpl.append(("lit", c))
            continue
        m = PREFIX.match(line)
        if m:
            tmpl.append(("lit", m.group(1))); line = line[m.end():]
        sents = splitter(line)
        for si, s in enumerate(sents):
            if si:
                tmpl.append(("lit", " "))
            tmpl.append(("tr", s) if re.search(r"[^\W\d_]", s) else ("lit", s))
    return tmpl


def split_target(lang):
    def f(t):
        pat = r"(?<=[។៕!?])\s*" if lang == "khm" else r"(?<=[.!?])\s+"
        return [s for s in re.split(pat, t.strip()) if s.strip()]
    return f


def fill(tmpl, outs):
    it = iter(outs)
    return "".join(next(it) if k == "tr" else v for k, v in tmpl)


# ---------------------------------------------------------------- NLLB
class Nllb:
    def __init__(self, model_id=NLLB_ID):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id, dtype=torch.float16).to("cuda").eval()

    def _fit(self, pieces, limit=200):
        """Pieces longer than `limit` tokens (no sentence punctuation) are cut at spaces so nothing is truncated."""
        out, owner = [], []
        for i, p in enumerate(pieces):
            n = len(self.tok(p)["input_ids"])
            k = (n + limit - 1) // limit
            if k <= 1:
                out.append(p); owner.append(i); continue
            words = p.split(" ")
            if len(words) < k:                                            # no spaces: cut by characters
                step = (len(p) + k - 1) // k
                parts = [p[j:j + step] for j in range(0, len(p), step)]
            else:
                step = (len(words) + k - 1) // k
                parts = [" ".join(words[j:j + step]) for j in range(0, len(words), step)]
            out += parts; owner += [i] * len(parts)
        return out, owner

    def tr(self, pieces, src, tgt, bs=32):
        if not pieces:
            return []
        torch, tok = self.torch, self.tok
        texts, owner = self._fit(pieces)
        tok.src_lang = src
        bos = tok.convert_tokens_to_ids(tgt)
        order = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
        res = [None] * len(texts)
        with torch.no_grad():
            for s in range(0, len(order), bs):
                idx = order[s:s + bs]
                enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True, truncation=True,
                          max_length=256).to("cuda")
                mx = min(400, int(enc["input_ids"].shape[1] * 3) + 16)
                g = self.model.generate(**enc, forced_bos_token_id=bos, num_beams=4, max_new_tokens=mx)
                for i, t in zip(idx, tok.batch_decode(g, skip_special_tokens=True)):
                    res[i] = t.strip()
            for i, t in enumerate(res):                                    # retry runaway repetitions once
                if loop_text(t):
                    enc = tok([texts[i]], return_tensors="pt", truncation=True, max_length=256).to("cuda")
                    g = self.model.generate(**enc, forced_bos_token_id=bos, num_beams=4, no_repeat_ngram_size=3,
                                            max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
                    res[i] = tok.decode(g[0], skip_special_tokens=True).strip()
        joined = collections.defaultdict(list)
        for i, t in zip(owner, res):
            joined[i].append(t)
        return [" ".join(joined[i]) for i in range(len(pieces))]

    def translate_docs(self, docs, src_lang, tgt_lang, splitter, repair=False):
        tmpls = [segment(d, splitter) for d in docs]
        flat = [v for t in tmpls for k, v in t if k == "tr"]
        if src_lang == "eng_Latn":
            outs = self.tr([normalize_en(x) for x in flat], src_lang, tgt_lang)
            if repair:
                outs = [repair_decimals(a, b) for a, b in zip(flat, outs)]
        else:
            outs = self.tr(flat, src_lang, tgt_lang)
        it = iter(outs)
        return [fill(t, [next(it) for k, _ in t if k == "tr"]) for t in tmpls]


# ---------------------------------------------------------------- LLMs
def stop_ids(tok):
    """eos plus the end-of-turn token: Sailor2 ends a reply with <|im_end|> but its generation eos is <|endoftext|>
    (added 2026-11-27; outputs saved before that were not rerun)."""
    ids = {tok.eos_token_id} | {tok.convert_tokens_to_ids(t) for t in ("<|im_end|>", "<end_of_turn>", "<|eot_id|>")}
    return sorted(i for i in ids if i is not None and i != tok.unk_token_id)


def llm_generate(model, tok, proc, system, texts, max_new, bs):
    import torch
    ps = []
    for t in texts:
        if proc is None:                                              # text-only model: plain string content
            msgs = [{"role": "system", "content": system}, {"role": "user", "content": t}]
            ps.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        else:
            msgs = [{"role": "system", "content": [{"type": "text", "text": system}]},
                    {"role": "user", "content": [{"type": "text", "text": t}]}]
            ps.append(proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    lens = [len(tok(p, add_special_tokens=False)["input_ids"]) for p in ps]
    order = sorted(range(len(ps)), key=lambda i: -lens[i])
    res = [None] * len(ps)
    for s in range(0, len(order), bs):
        idx = order[s:s + bs]
        mx = max_new([texts[i] for i in idx])
        enc = tok([ps[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        with torch.no_grad():
            g = model.generate(**enc, do_sample=False, temperature=None, top_p=None, top_k=None,
                               repetition_penalty=None, max_new_tokens=mx, pad_token_id=tok.pad_token_id,
                               eos_token_id=stop_ids(tok))
        for i, row in zip(idx, g[:, enc["input_ids"].shape[1]:]):
            n = int((row != tok.pad_token_id).sum())
            res[i] = {"raw": tok.decode(row, skip_special_tokens=True), "new_tokens": n, "hit_max": n >= mx}
    return res


def budget(tok, factor, cap=4096):
    """max_new_tokens for a batch: `factor` x the longest input (Qwen spends ~6.6 tokens on Khmer per English token)."""
    return lambda texts: min(cap, int(factor * max(len(tok(t)["input_ids"]) for t in texts)) + 64)


def token_ratio(tok, lk, n=100):
    """Target-language tokens per English token for this tokenizer, on the first n FLORES devtest sentences
    (Khmer: Gemma 2.9, Qwen 6.7, Apertus 15.2), so the output budget fits each model's tokenizer."""
    fl = os.path.join(TA.FL, "{}.devtest")
    en = open(fl.format("eng_Latn"), encoding="utf-8").read().splitlines()[:n]
    tg = open(fl.format(LANGS[lk][1]), encoding="utf-8").read().splitlines()[:n]
    cnt = lambda xs: sum(len(tok(x, add_special_tokens=False)["input_ids"]) for x in xs)
    return cnt(tg) / cnt(en)


def clean_fwd(raw):
    """Drop <think>, code fences, an English preamble line ('Here is the Khmer translation:') and trailing notes."""
    t = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S).strip()
    t = re.sub(r"^```\w*\n|\n```$", "", t).strip()
    lines = t.split("\n")
    while lines and re.search(r"(translat|here is|here's)[^\n]*:\s*$", lines[0], re.I) and lines[0].isascii():
        lines.pop(0)
    t = "\n".join(lines).strip()
    t = re.split(r"\n\s*\n\s*[\(*_]*\s*(?:note|notes|translator'?s? note)\b", t, maxsplit=1, flags=re.I)[0]
    return t.strip()


def loop_text(t):
    """A run of >= 20 characters repeated 4 times in a row (works for scripts without word spaces)."""
    m = re.search(r"(.{20,}?)\1{3,}", t or "", re.S)          # ignore table padding (runs of spaces / dashes)
    return bool(m) and bool(re.search(r"[^\W\d_]", m.group(1)))


# ---------------------------------------------------------------- GPU run
def fwd_path(sysname, lk):
    return os.path.join(D, "fwd", f"{slug(sysname)}.{lk}.jsonl")


def bt_path(sysname, lk, back):
    return os.path.join(D, "bt", f"{slug(sysname)}.{lk}.by_{slug(back)}.jsonl")


def run_gpu(chunks, bs):
    os.environ.setdefault("USE_TF", "0")
    import gc
    import torch
    src = [c["text"] for c in chunks]
    nl = Nllb()
    log(f"{NLLB} loaded")
    for lk, (lname, code) in LANGS.items():                          # NLLB forward
        p = fwd_path(NLLB, lk)
        if os.path.exists(p):
            continue
        t0 = time.time()
        out = nl.translate_docs(src, "eng_Latn", code, lambda s: split_en(s, fixed=True), repair=True)
        sec = (time.time() - t0) / len(src)
        write_jsonl(p, [{"id": c["id"], "raw": o, "text": o, "hit_max": False, "sec_per_chunk": round(sec, 2)}
                        for c, o in zip(chunks, out)])
        log(f"  {NLLB} en->{lk}: {sec:.2f} s/chunk")
    for name, mid in NLLB_FWD_EXTRA.items():                          # other NLLB sizes, forward only
        need = [lk for lk in LANGS if name in SYSTEMS and not os.path.exists(fwd_path(name, lk))]
        if not need:
            continue
        t0 = time.time()
        other = Nllb(mid)
        log(f"{name} loaded in {time.time() - t0:.0f} s")
        for lk in need:
            t1 = time.time()
            out = other.translate_docs(src, "eng_Latn", LANGS[lk][1], lambda s: split_en(s, fixed=True), repair=True)
            sec = (time.time() - t1) / len(src)
            write_jsonl(fwd_path(name, lk), [{"id": c["id"], "raw": o, "text": o, "hit_max": False,
                                              "sec_per_chunk": round(sec, 2)} for c, o in zip(chunks, out)])
            log(f"  {name} en->{lk}: {sec:.2f} s/chunk")
        del other
        gc.collect(); torch.cuda.empty_cache()
    for name in (n for n in LLM_PATH if n in SYSTEMS):                 # LLM forward (+ SEA-LION back-translation)
        need_fwd = [lk for lk in LANGS if not os.path.exists(fwd_path(name, lk))]
        need_bt = [(s, lk) for s in SYSTEMS for lk in LANGS if not os.path.exists(bt_path(s, lk, SEAL))] \
            if name == SEAL else []
        if not need_fwd and not need_bt:
            continue
        t0 = time.time()
        model, tok, proc = TA.load_llm(*LLM_PATH[name])
        log(f"{name} loaded in {time.time() - t0:.0f} s")
        for lk in need_fwd:
            lname = LANGS[lk][0]
            t1 = time.time()
            res = llm_generate(model, tok, proc, FWD_SYSTEM.format(lang=lname), src,
                               budget(tok, 1.5 * token_ratio(tok, lk), cap=8192), bs)
            sec = (time.time() - t1) / len(src)
            write_jsonl(fwd_path(name, lk), [{"id": c["id"], **r, "text": clean_fwd(r["raw"]), "sec_per_chunk": round(sec, 2)}
                                             for c, r in zip(chunks, res)])
            log(f"  {name} en->{lk}: {sec:.2f} s/chunk, hit max {sum(r['hit_max'] for r in res)}")
        if name == SEAL:
            for s, lk in [(s, lk) for s in SYSTEMS for lk in LANGS if (s, lk) in need_bt]:
                hyp = [r["text"] or "(empty)" for r in read_jsonl(fwd_path(s, lk))]
                res = llm_generate(model, tok, proc, TA.SYSTEM.format(lang=LANGS[lk][0]), hyp, budget(tok, 3, 2048), bs)
                write_jsonl(bt_path(s, lk, SEAL), [{"id": c["id"], "text": TA.clean(r["raw"]), "hit_max": r["hit_max"]}
                                                    for c, r in zip(chunks, res)])
                log(f"  back-translated {s} {lk} by {SEAL}")
        del model
        gc.collect(); torch.cuda.empty_cache()
    for s in SYSTEMS:                                                  # NLLB back-translation
        for lk, (_, code) in LANGS.items():
            p = bt_path(s, lk, NLLB)
            if os.path.exists(p):
                continue
            hyp = [r["text"] for r in read_jsonl(fwd_path(s, lk))]
            out = nl.translate_docs(hyp, code, "eng_Latn", split_target(lk))
            write_jsonl(p, [{"id": c["id"], "text": o} for c, o in zip(chunks, out)])
            log(f"  back-translated {s} {lk} by {NLLB}")
    del nl
    gc.collect(); torch.cuda.empty_cache()


def comet(chunks, gpu):
    """Round-trip COMET per system/lang/back-translator, cached by a hash of the inputs."""
    cf = os.path.join(D, "comet.json")
    cache = json.load(open(cf)) if os.path.exists(cf) else {}
    jobs = {}
    for s in SYSTEMS:
        for lk in LANGS:
            for b in BACK:
                fw, bt = read_jsonl(fwd_path(s, lk)), read_jsonl(bt_path(s, lk, b))
                if len(fw) != len(chunks) or len(bt) != len(chunks):
                    continue
                batch = [{"src": f["text"], "mt": t["text"], "ref": c["text"]} for c, f, t in zip(chunks, fw, bt)]
                h = hashlib.sha1(json.dumps(batch, ensure_ascii=False).encode()).hexdigest()[:12]
                if cache.get(f"{s}|{lk}|{b}|hash") != h:
                    jobs[(s, lk, b)] = (batch, h)
    if jobs and gpu:
        sys.path.insert(0, TA.COMET_LIB)
        from comet import download_model, load_from_checkpoint
        cm = load_from_checkpoint(download_model("Unbabel/wmt22-comet-da"))
        for (s, lk, b), (batch, h) in jobs.items():
            o = cm.predict(batch, batch_size=32, gpus=1, progress_bar=False)
            cache[f"{s}|{lk}|{b}"] = [round(float(x), 4) for x in o.scores]
            cache[f"{s}|{lk}|{b}|hash"] = h
            log(f"  COMET {s} {lk} by {b}: {sum(o.scores) / len(o.scores):.4f}")
        json.dump(cache, open(cf, "w"))
    elif jobs:
        log(f"COMET missing or stale for {list(jobs)} (needs the GPU job)")
        for k in jobs:
            cache.pop("|".join(k), None)
    return cache


# ---------------------------------------------------------------- scoring
def right_script(t, lk):
    letters = [ch for ch in t if ch.isalpha()]
    if not letters:
        return False
    if lk in SCRIPT_RE:
        return len(SCRIPT_RE[lk].findall(t)) >= 0.5 * len(letters)
    return len(VI_MARKS.findall(t)) >= 0.08 * len(letters)


def score(chunks, cm):
    import sacrebleu
    rows, per = [], collections.defaultdict(dict)
    for lk, (lname, _) in LANGS.items():
        for s in SYSTEMS + REPORT_ONLY:
            fw = read_jsonl(fwd_path(s, lk))
            if len(fw) != len(chunks):
                continue
            A = collections.Counter()
            for c, f in zip(chunks, fw):
                en, tg = c["text"], f["text"]
                bts = {b: (read_jsonl(bt_path(s, lk, b)) or [{}] * len(chunks))[c["id"]].get("text", "") for b in BACK}
                n_en, _ = numbers(en)
                st, lo = numbers(tg, lk)
                hn = max(multiset_hits(n_en, st), multiset_hits(n_en, lo))
                A["num_total"] += len(n_en); A["num_ok"] += hn
                A["num_spurious"] += max(0, len(st) - multiset_hits(n_en, st))
                neg_ok = True
                if EN_NEG.search(en):
                    A["neg_chunks"] += 1
                    neg_ok = bool(TGT_NEG[lk].search(tg))
                    A["neg_ok"] += neg_ok
                drugs_ok = True
                for dr in (m.lower() for m in DRUG_RE.findall(en)):
                    in_tg = drug_found(dr, tg)
                    ok = in_tg is not None or any(drug_found(dr, b) for b in bts.values())
                    A["drug_total"] += 1; A["drug_latin"] += in_tg is not None; A["drug_ok"] += ok
                    drugs_ok &= ok
                u_en = [u.lower() for u in units(en)]
                hu = multiset_hits(u_en, [u.lower() for u in units(tg)])
                A["unit_total"] += len(u_en); A["unit_ok"] += hu
                script = right_script(tg, lk)
                loop = f.get("hit_max", False) or loop_text(tg)
                A["wrong_script"] += not script; A["loops"] += loop; A["empty"] += not tg.strip()
                ok = hn == len(n_en) and neg_ok and drugs_ok and hu == len(u_en) and script and not loop
                A["all_ok"] += ok
                per[c["id"]][f"{s}|{lk}"] = {"text": tg, "back": bts, "all_ok": ok}
            r = {"system": s, "lang": lk, "language": lname, "n": len(chunks), **A,
                 "sec_per_chunk": fw[0].get("sec_per_chunk")}
            for b in BACK:
                bt = read_jsonl(bt_path(s, lk, b))
                if len(bt) == len(chunks):
                    r[f"bt_chrF++|{b}"] = round(sacrebleu.corpus_chrf([x["text"] for x in bt], [[c["text"] for c in chunks]],
                                                                      word_order=2).score, 2)
                    r[f"bt_BLEU|{b}"] = round(sacrebleu.corpus_bleu([x["text"] for x in bt], [[c["text"] for c in chunks]]).score, 2)
                sc = cm.get(f"{s}|{lk}|{b}")
                r[f"bt_COMET|{b}"] = round(sum(sc) / len(sc), 4) if sc else None
            rows.append(r)
    return rows, per


def pct(a, b):
    return f"{100 * a / b:.1f}% ({a}/{b})" if b else "n/a"


def report(rows, per, chunks, path):
    mix = dict(collections.Counter(c["source_type"] for c in chunks))
    L = ["# Reverse translation test (English → Khmer / Lao / Vietnamese), 100 guideline chunks", "",
         f"100 random chunks of `out/pipeline/stage4_chunk/chunks_256.jsonl` (seed 0; {mix}; author lists, Qwen3 image "
         "descriptions and chunks over 384 tokens left out). There is no human translation of the guideline, so:", "",
         "- **Checks on the translation**: numbers kept (locale-aware, 0,5 = 0.5), negation cue present when the English "
         "has one, drug names in Latin script (or recovered in a back-translation), units, right script, loops.",
         "- **Round trip**: each translation is back-translated to English by NLLB-1.3B and by SEA-LION and compared "
         "with the English chunk (chrF++, COMET). A system back-translated by itself may be favoured; read the two "
         "back-translator columns together.", "",
         "NLLB: fixed mt_safety pipeline (sentence by sentence, table cells one by one, beam 4, decimals repaired). "
         "LLMs (Qwen3-VL-8B and the SEA-LION v4 models): whole chunk in one prompt, greedy, told to keep numbers, negations, drug names "
         "in Latin script and the markdown layout.", ""]
    for lk, (lname, _) in LANGS.items():
        L += [f"## English → {lname}", "",
              "| system | all checks pass | numbers kept | extra numbers | negation present | drug names Latin | "
              "drug names OK (Latin or BT) | units kept | wrong script | loops | BT chrF++ (NLLB / SEA-LION) | "
              "BT COMET (NLLB / SEA-LION) | s / chunk |", "|---" * 13 + "|"]
        for r in (x for x in rows if x["lang"] == lk):
            f = lambda k: "-" if r.get(k) is None else f"{r[k]}"
            L.append(f"| {r['system']} | {pct(r['all_ok'], r['n'])} | {pct(r['num_ok'], r['num_total'])} | "
                     f"{r['num_spurious']} | {pct(r['neg_ok'], r['neg_chunks'])} | {pct(r['drug_latin'], r['drug_total'])} | "
                     f"{pct(r['drug_ok'], r['drug_total'])} | {pct(r['unit_ok'], r['unit_total'])} | {r['wrong_script']} | "
                     f"{r['loops']} | {f('bt_chrF++|' + NLLB)} / {f('bt_chrF++|' + SEAL)} | "
                     f"{f('bt_COMET|' + NLLB)} / {f('bt_COMET|' + SEAL)} | {f('sec_per_chunk')} |")
        L.append("")
    L += ["## Examples (shortest chunks with a number), with the NLLB back-translation", ""]
    ex = sorted((c for c in chunks if re.search(r"\d", c["text"])), key=lambda c: len(c["text"]))[:3]
    for c in ex:
        L += [f"### {c['citation']}", "", "English: " + c["text"].replace("\n", " / "), ""]
        for lk, (lname, _) in LANGS.items():
            for s in SYSTEMS:
                d = per[c["id"]].get(f"{s}|{lk}")
                if d:
                    L.append(f"- {lname}, {s}{'' if d['all_ok'] else ' (fails a check)'}: {d['text'][:400].replace(chr(10), ' / ')}"
                             f"  \n  ↳ back ({NLLB}): {d['back'][NLLB][:400].replace(chr(10), ' / ')}")
        L.append("")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")


def chart(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {NLLB: "#257de0", QWEN: "#ee7fac", SEAL: "#008a17",      # same colours as translation_agent_bleu.png
              QSL4: "#7a5af8", GSL4: "#b0413e", APSL: "#5f6b7a",
              S2_3: "#9c36b5", S2_8: "#5c940d", S2_20: "#3b2a8a", NLLB33: "#0b3d91"}
    langs = [lk for lk in LANGS if any(r["lang"] == lk for r in rows)]
    panels = [("all checks pass (%)", lambda r: 100 * r["all_ok"] / r["n"], 0, "{:.0f}"),
              ("numbers kept (%)", lambda r: 100 * r["num_ok"] / max(1, r["num_total"]), 0, "{:.1f}"),
              (f"round-trip COMET, back-translated by {NLLB}\naxis starts at 0.4", lambda r: r.get(f"bt_COMET|{NLLB}") or 0, 0.4, "{:.3f}"),
              (f"round-trip COMET, back-translated by {SEAL}\naxis starts at 0.4", lambda r: r.get(f"bt_COMET|{SEAL}") or 0, 0.4, "{:.3f}")]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), dpi=150)
    w = 0.8 / len(SYSTEMS)
    for ax, (title, fn, lo, fmt) in zip(axes.flat, panels):
        top = 0
        for j, s in enumerate(SYSTEMS):
            vals = [next((fn(r) for r in rows if r["system"] == s and r["lang"] == lk), 0) for lk in langs]
            top = max([top] + vals)
            xs = [i + (j - (len(SYSTEMS) - 1) / 2) * w for i in range(len(langs))]
            bars = ax.bar(xs, [max(0, v - lo) for v in vals], w * 0.92, bottom=lo, color=colors[s], label=s, zorder=2)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, max(v, lo), fmt.format(v), ha="center", va="bottom", fontsize=7, color="#444")
        ax.set_ylim(lo, top + (top - lo) * 0.12 + (0.01 if lo else 1))
        ax.set_xticks(range(len(langs)))
        ax.set_xticklabels([f"EN → {LANGS[lk][0]}" for lk in langs])
        ax.set_title(title, fontsize=9, loc="left")
        ax.grid(axis="y", color="#e5e5e5", zorder=0)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.spines["left"].set_color("#bbb"); ax.spines["bottom"].set_color("#bbb")
    axes[0, 0].legend(frameon=False, fontsize=8, ncol=6, loc="lower left", bbox_to_anchor=(0, 1.08))
    fig.suptitle("English → Khmer / Lao / Vietnamese on 100 guideline chunks", x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("HF_HOME", os.path.normpath(os.path.join(ROOT, "..", "hf_cache")))
    chunks = select()
    if not a.report_only:
        run_gpu(chunks, a.bs)
    cm = comet(chunks, gpu=not a.report_only)
    rows, per = score(chunks, cm)
    json.dump({"config": {"chunks": len(chunks), "systems": SYSTEMS, "back_translators": BACK, "llm_prompt": FWD_SYSTEM},
               "scores": rows}, open(os.path.join(OUT, "reverse_mt_results.json"), "w"), indent=1, ensure_ascii=False)
    report(rows, per, chunks, os.path.join(OUT, "reverse_mt_report.md"))
    chart(rows, os.path.join(OUT, "reverse_mt.png"))
    log("wrote out/reverse_mt_report.md, out/reverse_mt_results.json, out/reverse_mt.png")


if __name__ == "__main__":
    main()
