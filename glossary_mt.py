"""Glossary-augmented NLLB translation (EN -> km/lo/vi).

Pipeline per sentence: find glossary terms -> replace each with a placeholder -> translate with NLLB
-> put the target-language glossary term back where the placeholder ended up.

    python glossary_mt.py --placeholder-test   # GPU: which placeholder format survives NLLB? (no glossary needed)

Outputs in out/glossary_mt/.
"""
import os, re, sys, json, argparse, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from mt_safety_test import read_jsonl, write_jsonl, split_en, normalize_en, CHUNKS, LANGS, ENG, MODEL_ID

OUT = os.path.join(ROOT, "out", "glossary_mt")

# Terms that NLLB mistranslated in the safety test (out/mt_safety/REPORT.md). Only used to choose
# *where* to put placeholders in the survival test; the target-language side is not needed for that.
SEED_TERMS = ["intubation", "intubate", "intramuscularly", "intramuscular", "IM", "IV", "intravenous",
              "hypertonic saline", "saline", "infusion", "bolus", "hypotension", "hypoglycemia",
              "contraindicated", "contraindication", "contraindications", "dialysis", "mechanical ventilation",
              "transfusion", "orally", "neonate", "infant", "wean", "anticoagulant", "eGFR"]

# Placeholder formats to compare. {i} = 1-based index.
FORMATS = {
    "bracket":  "[TERM_{i}]",   # the format from the spec
    "plain":    "TERM{i}",
    "xml":      "<t{i}>",
    "pseudo":   None,           # drug-like pseudo-names (NLLB copies Latin drug names well)
}
PSEUDO = ["Zorvex", "Quilmar", "Brevant", "Taxolin", "Mirdaz", "Pelvox", "Corbane", "Ludrex", "Fenquil", "Varmox"]


def placeholder(fmt, i):
    return PSEUDO[i - 1] if fmt == "pseudo" else FORMATS[fmt].format(i=i)


def term_regex(terms):
    terms = sorted(terms, key=len, reverse=True)
    # case-sensitive for abbreviations (IM, IV), case-insensitive for words
    parts = [re.escape(t) if t.isupper() else "(?i:" + re.escape(t) + ")" for t in terms]
    return re.compile(r"(?<![\w-])(" + "|".join(parts) + r")(?![\w-])")


def mask(sentence, rx, fmt):
    """Replace glossary terms with numbered placeholders. Returns masked text and the list of terms."""
    found = []
    def sub(m):
        if len(found) >= len(PSEUDO):
            return m.group(0)
        found.append(m.group(0))
        return placeholder(fmt, len(found))
    return rx.sub(sub, sentence), found


def placeholder_test():
    os.environ["USE_TF"] = "0"
    import torch, numpy as np
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, dtype=torch.float16).to("cuda").eval()

    @torch.no_grad()
    def tr(texts, tgt, bs=32):
        tok.src_lang = ENG
        out = []
        for s in range(0, len(texts), bs):
            enc = tok(texts[s:s + bs], return_tensors="pt", padding=True, truncation=True, max_length=256).to("cuda")
            g = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(tgt), num_beams=4,
                               max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
            out += [t.strip() for t in tok.batch_decode(g, skip_special_tokens=True)]
        return out

    rx = term_regex(SEED_TERMS)
    sents = [s for r in read_jsonl(CHUNKS) for s in split_en(normalize_en(r["text"]), fixed=True)]
    rows, summary = [], {}
    for fmt in FORMATS:
        masked = [mask(s, rx, fmt) for s in sents]
        idx = [k for k, (_, f) in enumerate(masked) if f]          # sentences with >= 1 term
        src = [masked[k][0] for k in idx]
        for lk, (_, code) in LANGS.items():
            hyp = tr(src, code)
            n_ph = n_ok = n_sent_ok = 0
            for k, h in zip(idx, hyp):
                terms = masked[k][1]
                ok_all = True
                for i in range(1, len(terms) + 1):
                    c = h.count(placeholder(fmt, i))
                    n_ph += 1; n_ok += c == 1; ok_all &= c == 1
                n_sent_ok += ok_all
                rows.append({"fmt": fmt, "lang": lk, "src": masked[k][0], "terms": terms, "hyp": h})
            summary[f"{fmt}/{lk}"] = {"placeholders_exactly_once": f"{n_ok}/{n_ph}",
                                      "pct": round(100 * n_ok / n_ph, 1),
                                      "sentences_all_ok": f"{n_sent_ok}/{len(idx)}"}
            print(fmt, lk, summary[f"{fmt}/{lk}"], flush=True)
    os.makedirs(OUT, exist_ok=True)
    write_jsonl(os.path.join(OUT, "placeholder_test.jsonl"), rows)
    json.dump(summary, open(os.path.join(OUT, "placeholder_test_summary.json"), "w"), indent=1)




# ---------------------------------------------------------------- glossary-augmented translation
GLOSSARY = os.path.join(ROOT, "data", "medical_glossary.json")
# Kept verbatim in every language: drug names + clinical abbreviations / score names.
ABBREV = """IM IV PO SC eGFR GCS NYHA qSOFA SOFA SpO2 PCO2 PaCO2 PAP HFNC LMWH GDMT SGLT2i HHS NAC ICP CPP CBF LVEF HF VT VF
DHP CCBs CCB HTN CKD pRBCs NIHSS TIMI STEMI COPD ABCs IE NVE PVE HLAR PE MAP ROX NEWS ECG INR LPM""".split()


def load_terms(lang, protect_only=False):
    """{english surface form: replacement} for one target language: protected terms map to themselves."""
    from mt_safety_test import DRUGS
    terms = {d: None for d in DRUGS}                    # None = keep the source spelling
    terms.update({a: None for a in ABBREV})
    for g in ([] if protect_only else json.load(open(GLOSSARY))):
        if g["use"].get(lang) and g.get(lang):
            t = g[lang]
            if lang == "vie" or lang == "vi":
                t = t[0].lower() + t[1:]
            terms[g["en"]] = t
    return terms


LANG2 = {"khm": "km", "lao": "lo", "vie": "vi"}


def build_masker(terms):
    rx = term_regex(list(terms))
    lower = {k.lower(): v for k, v in terms.items()}
    if all(v is None for v in terms.values()):
        # protect-only: one placeholder per run of protected tokens ('DHP CCBs', 'non-DHP-CCBs'),
        # so NLLB cannot reorder the pieces of a noun phrase
        one = rx.pattern[len("(?<![\\w-])("):-len(")(?![\\w-])")]
        rx = re.compile(r"(?<![\w-])(?:%s)(?:[\s/-]+(?:%s))*(?![\w-])" % (one, one))

    def mask_sent(s):
        found = []
        def sub(m):
            w = m.group(0)
            pre, post = s[max(0, m.start() - 4):m.start()], s[m.end():m.end() + 1]
            if w == "IV" and (pre.endswith("/") or pre.endswith("III") or post == "/"):   # NYHA class III/IV
                return w
            rep = lower.get(w.lower()) if w.lower() in lower else None
            found.append(w if rep is None else rep)
            return f"TERM{len(found)}"
        return rx.sub(sub, s), found
    return mask_sent


def restore(hyp, found):
    """Put replacements back. Returns None if any placeholder is missing or duplicated (caller falls back)."""
    for i, rep in sorted(enumerate(found, 1), reverse=True):        # TERM10 before TERM1
        pat = re.compile(r"TERM\s?%d(?!\d)" % i, re.I)
        if len(pat.findall(hyp)) != 1:
            return None
        hyp = pat.sub(lambda _: rep, hyp)
    return hyp


def translate_glossary(protect_only=False):
    os.environ["USE_TF"] = "0"
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from mt_safety_test import TRANS
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, dtype=torch.float16).to("cuda").eval()
    stats = collections.Counter()

    def looped(t):
        w = t.split() if " " in t else list(t)
        g = collections.Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
        return bool(g) and g.most_common(1)[0][1] >= 5

    @torch.no_grad()
    def tr(texts, src, tgt, bs=32):
        tok.src_lang = src
        bos = tok.convert_tokens_to_ids(tgt)
        out = []
        for s in range(0, len(texts), bs):
            enc = tok(texts[s:s + bs], return_tensors="pt", padding=True, truncation=True, max_length=256).to("cuda")
            g = model.generate(**enc, forced_bos_token_id=bos, num_beams=4,
                               max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
            out += [t.strip() for t in tok.batch_decode(g, skip_special_tokens=True)]
        for i, t in enumerate(out):                       # same loop retry as the 'fixed' variant
            if looped(t):
                enc = tok([texts[i]], return_tensors="pt", truncation=True, max_length=256).to("cuda")
                g = model.generate(**enc, forced_bos_token_id=bos, num_beams=4, no_repeat_ngram_size=3,
                                   max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
                out[i] = tok.decode(g[0], skip_special_tokens=True).strip()
                stats[f"loop_retry {tgt}"] += 1
        return out

    rows = read_jsonl(CHUNKS)
    sents = [split_en(normalize_en(r["text"]), fixed=True) for r in rows]
    lens = [len(x) for x in sents]
    flat = [s for x in sents for s in x]
    regroup = lambda xs: (lambda it: [[next(it) for _ in range(n)] for n in lens])(iter(xs))
    log = []
    for lk, (_, code) in LANGS.items():
        masker = build_masker(load_terms(LANG2[lk], protect_only))
        masked = [masker(s) for s in flat]
        hyp_m = tr([m for m, _ in masked], ENG, code)
        plain_idx = [i for i, (m, f) in enumerate(masked) if f]
        plain = dict(zip(plain_idx, tr([flat[i] for i in plain_idx], ENG, code)))   # fallback translations
        final = []
        for i, ((m, f), h) in enumerate(zip(masked, hyp_m)):
            if not f:
                final.append(h); continue
            r = restore(h, f)
            stats[f"{lk} sentences_with_terms"] += 1
            stats[f"{lk} terms"] += len(f)
            if r is None:
                stats[f"{lk} fallback_no_glossary"] += 1
                r = plain[i]
            final.append(r)
            log.append({"lang": lk, "en": flat[i], "masked": m, "terms": f, "hyp_masked": h, "final": r})
        back = tr(final, code, ENG)
        for r, en_s, f_s, b_s in zip(rows, sents, regroup(final), regroup(back)):
            r["sents_en"] = en_s
            r[f"sents_{lk}"], r[f"sents_{lk}_back"] = f_s, b_s
            r[lk], r[f"{lk}_back"] = " ".join(f_s), " ".join(b_s)
        print(lk, "done", flush=True)
    tag = "protect" if protect_only else "glossary"
    path = TRANS.replace(".jsonl", f"_{tag}.jsonl")
    write_jsonl(path, rows)
    os.makedirs(OUT, exist_ok=True)
    write_jsonl(os.path.join(OUT, f"{tag}_log.jsonl"), log)
    print(dict(stats)); print("wrote", path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--placeholder-test", action="store_true")
    ap.add_argument("--translate", action="store_true", help="glossary-augmented translation of the 50 safety-test chunks")
    ap.add_argument("--protect-only", action="store_true", help="only keep drug names + abbreviations verbatim (no glossary)")
    a = ap.parse_args()
    if a.translate:
        translate_glossary(a.protect_only)
    if a.placeholder_test:
        placeholder_test()
