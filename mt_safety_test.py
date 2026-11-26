"""Medical MT safety test: EN -> Khmer / Lao / Vietnamese with NLLB-200 1.3B.

Stages (each resumable, outputs in out/mt_safety/):
  python mt_safety_test.py --select      # login node: pick 50 guideline chunks from Chandra output -> chunks.jsonl
  python mt_safety_test.py --translate   # GPU (runai): EN->X and X->EN back-translation -> translations.jsonl
  python mt_safety_test.py --score       # login node: automatic checks -> report.json, per_chunk.jsonl, report.md

Checks per language: number / negation / drug-name / unit preservation in the translation,
the same facts in the back-translation, and BLEU + chrF++ of back-translation vs the English source.
"""
import os, re, sys, json, html, argparse, random, difflib, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out", "mt_safety")
CHUNKS = os.path.join(OUT, "chunks.jsonl")
TRANS = os.path.join(OUT, "translations.jsonl")
SRC_MD = os.path.join(ROOT, "out", "chandra_output.md")

MODEL_ID = "facebook/nllb-200-1.3B"
ENG = "eng_Latn"
LANGS = {"khm": ("Khmer", "khm_Khmr"), "lao": ("Lao", "lao_Laoo"), "vie": ("Vietnamese", "vie_Latn")}

# ---------------------------------------------------------------- lexicons
# INN drug names that occur in the guideline. Generic chemistry words (potassium, glucose, sodium,
# magnesium, charcoal, ...) are left out on purpose: translating those is correct, not an error.
DRUGS = """adrenaline epinephrine noradrenaline norepinephrine dopamine dobutamine vasopressin amiodarone adenosine
atropine lidocaine digoxin diltiazem verapamil metoprolol carvedilol bisoprolol propranolol labetalol esmolol
atenolol amlodipine nifedipine nicardipine hydralazine captopril enalapril lisinopril ramipril losartan valsartan
sacubitril spironolactone furosemide hydrochlorothiazide indapamide mannitol nitroglycerin nitroglycerine
isosorbide heparin enoxaparin warfarin rivaroxaban apixaban dabigatran aspirin clopidogrel ticagrelor
streptokinase alteplase tranexamic atorvastatin rosuvastatin insulin empagliflozin dapagliflozin glucagon
hydrocortisone dexamethasone methylprednisolone prednisolone prednisone fludrocortisone salbutamol theophylline
paracetamol acetaminophen ibuprofen morphine fentanyl ketamine propofol midazolam diazepam lorazepam phenytoin
phenobarbital carbamazepine haloperidol naloxone flumazenil n-acetylcysteine acetylcysteine pralidoxime
ceftriaxone cefotaxime ceftazidime cefazolin amoxicillin ampicillin penicillin cloxacillin piperacillin meropenem
imipenem vancomycin gentamicin ciprofloxacin metronidazole oseltamivir quinine isoniazid ranitidine
metoclopramide ondansetron thiamine lactulose allopurinol colchicine phentolamine deferoxamine""".split()
DRUG_RE = re.compile(r"(?<![A-Za-z-])(" + "|".join(sorted(map(re.escape, DRUGS), key=len, reverse=True)) + r")(?![A-Za-z])", re.I)

UNIT_CANON = {"mg": "mg", "mcg": "mcg", "µg": "mcg", "μg": "mcg", "ug": "mcg", "g": "g", "kg": "kg",
              "ml": "mL", "l": "L", "mmhg": "mmHg", "meq": "mEq", "mmol": "mmol", "iu": "IU", "units": "units"}
# a unit counts only when it sits right after a number or a slash (so "e.g." or "L" in words are not units)
UNIT_RE = re.compile(r"(?:(?<=\d)|(?<=\d )|(?<=/)|(?<=/ ))(mg|mcg|µg|μg|ug|kg|g|mL|ml|L|mmHg|mEq|mmol|IU)(?![A-Za-z])", re.I)

EN_NEG = re.compile(r"\b(not|never|cannot|avoid\w*|contraindicat\w*)\b|n't\b", re.I)
TGT_NEG = {
    # Khmer has no word spaces -> substring match. មិន not, កុំ don't, ហាម forbid, ពុំ not (formal),
    # គ្មាន none, ឥត without, ជៀសវាង/ចៀសវាង avoid
    "khm": re.compile(r"មិន|កុំ|ហាម|ពុំ|គ្មាន|ឥត|ជៀសវាង|ចៀសវាង"),
    # Lao: ບໍ່ not, ຢ່າ don't (but not ຢ່າງ 'way/like'), ຫ້າມ forbid, ຫຼີກ/ຫລີກ avoid, ປາສະຈາກ without
    "lao": re.compile(r"ບໍ່|ບໍ|ຢ່າ(?!ງ)|ຫ້າມ|ຫຼີກ|ຫລີກ|ປາສະຈາກ"),
    # Vietnamese: không not, chẳng/chưa not(yet), đừng/chớ don't, cấm forbid, tránh avoid, chống chỉ định contraindicated
    "vie": re.compile(r"\b(không|chẳng|chưa|đừng|chớ|cấm|tránh|chống chỉ định)\b", re.I),
}

SCORES = r"GCS|Glasgow|NEWS|qSOFA|SOFA|CURB-?65|CRB-?65|Wells|CHA2DS2|CHA₂DS₂|HAS-BLED|ROX|APGAR|Child[- ]Pugh|TIMI|GRACE|MELD|NIHSS|Killip|NYHA|Blatchford|Rockall|PESI|Centor|score"
CATEGORIES = {
    "dosage": lambda s: bool(UNIT_RE.search(s)) and bool(DRUG_RE.search(s))
                        and bool(re.search(r"\b(IV|IM|PO|SC|q\d+h|every|daily|infusion|bolus|dose|over|/day|/h)\b", s, re.I)),
    "negation": lambda s: bool(EN_NEG.search(s)),
    "conditional": lambda s: bool(re.search(r"\b(if|unless|when)\b", s, re.I)) and bool(re.search(r"[<>≤≥]|\d", s)),
    "scoring": lambda s: bool(re.search(r"\b(" + SCORES + r")\b", s)) and bool(re.search(r"[<>≤≥]|\b\d+\b", s)),
    "drug": lambda s: len({m.lower() for m in DRUG_RE.findall(s)}) >= 2,
}

# Clinical terms whose meaning must survive (checked in the back-translation; a paraphrase counts as a miss,
# so this is a lower bound). Added after the first run showed intubation/IM/saline errors the 5 checks miss.
CLIN_TERMS = {"intubation": r"intubat", "IM/intramuscular": r"\bIM\b|intramuscular", "IV/intravenous": r"\bIV\b|\bi\.v\.|intravenous",
              "orally/PO": r"\borally\b|\bPO\b|by mouth|\boral\b", "bolus": r"bolus", "infusion": r"infusion", "saline": r"saline",
              "dialysis": r"dialysis", "ventilation": r"ventilat", "transfusion": r"transfus", "hypotension": r"hypotens",
              "hypoglycemia": r"hypoglyc", "daily": r"daily|a day|per day", "contraindicat": r"contraindicat", "eGFR": r"eGFR",
              "anticoag/antiplatelet": r"anticoag|antiplatelet|anti-platelet"}

DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩໐໑໒໓໔໕໖໗໘໙", "01234567890123456789")


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def write_jsonl(p, rows):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def split_en(text, fixed=False):
    """Sentence split; translation is done per sentence so back-translation stays aligned.
    raw: the original splitter (misses 'LPM. Next' and 'ventilation.Wean'; NLLB then drops one sentence).
    fixed: split after any word, also when the space after the period is missing; keep i.v./e.g. together."""
    if not fixed:
        parts = re.split(r'(?<=[a-z0-9)%][.!?])\s+(?=[A-Z(])', text)
    else:
        text = re.sub(r"(?<=[a-z0-9)%])\.(?=[A-Z][a-z])", ". ", text)
        parts = re.split(r'(?<!\b[a-zA-Z]\.[a-zA-Z]\.)(?<!\bex\.)(?<=[\w)%\]][.!?])\s+(?=[A-Z(])', text)
    return [p.strip() for p in parts if p.strip()]


def normalize_en(text):
    """NLLB's vocabulary has no en/em dash or minus sign: they become <unk> and vanish,
    so '30–35 mm Hg' comes out as '3035 mm Hg'. Map them to ASCII hyphen before translating."""
    return re.sub(r"[\u2010-\u2015\u2212]", "-", text)


def repair_decimals(src, tgt):
    """NLLB detokenises '0.5' as '0, 5' / '0. 5'. For every decimal in the source, remove the space
    inside the matching target number (in ASCII, Khmer or Lao digits). Lists like '1, 2' are untouched
    unless the source itself has the decimal 1.2."""
    digit_sets = ["0123456789", "០១២៣៤៥៦៧៨៩", "໐໑໒໓໔໕໖໗໘໙"]
    for a, b in set(re.findall(r"(?<![\d.,])(\d+)[.,](\d+)(?![\d])", src)):
        for ds in digit_sets:
            A = a.translate(str.maketrans("0123456789", ds)); B = b.translate(str.maketrans("0123456789", ds))
            tgt = re.sub(r"(?<![\d%s])(%s)\s*([.,])\s+(%s)(?![\d%s])" % (ds, A, B, ds), r"\1\2\3", tgt)
    return tgt


# ---------------------------------------------------------------- stage 1: select
def select(n_per_cat=10, seed=0):
    t = open(SRC_MD, encoding="utf-8").read()
    t = re.sub(r"<table.*?</table>", "", t, flags=re.S)     # table cells lose their context; use prose
    t = re.sub(r"<img[^>]*>", "", t)
    units = re.split(r"</?(?:p|li|ul|ol|div|h\d)[^>]*>|\n", t)
    units = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", u))).strip() for u in units]
    seen, cand = set(), []
    for u in units:
        if not u or u in seen or re.search(r"[ក-៿]", u):
            continue
        seen.add(u)
        latin = sum(c.isascii() for c in u) / len(u)
        if latin > 0.9 and 10 <= len(u.split()) <= 60 and u[0].isalnum() or u[:1] in "☐•-":
            if 10 <= len(u.split()) <= 60:
                cand.append(re.sub(r"^[☐•\-\s]+", "", u))
    exclude = set(read_jsonl(os.path.join(OUT, "exclude.jsonl"))[0]["texts"]) if os.path.exists(os.path.join(OUT, "exclude.jsonl")) else set()
    cand = [c for c in cand if c not in exclude]
    rng = random.Random(seed)
    chosen, rows = set(), []
    for cat, f in CATEGORIES.items():
        pool = [c for c in cand if f(c) and c not in chosen]
        # prefer chunks that also carry other categories (denser test), then random
        rng.shuffle(pool)
        pool.sort(key=lambda c: -sum(g(c) for g in CATEGORIES.values()))
        for c in pool[:n_per_cat]:
            chosen.add(c)
            rows.append({"id": len(rows), "selected_for": cat, "text": c,
                         "tags": [k for k, g in CATEGORIES.items() if g(c)]})
        print(f"{cat:<12} {len(pool):4d} candidates")
    write_jsonl(CHUNKS, rows)
    print(f"wrote {len(rows)} chunks -> {CHUNKS}")


# ---------------------------------------------------------------- stage 2: translate (GPU)
def translate(variant="raw"):
    os.environ["USE_TF"] = "0"
    import torch, numpy as np
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16).to("cuda").eval()
    print("loaded", MODEL_ID, torch.cuda.get_device_name(0), flush=True)
    n_hit = collections.Counter()

    def looped(t):
        w = t.split() if " " in t else list(t)
        grams = collections.Counter(tuple(w[i:i + 3]) for i in range(len(w) - 2))
        return bool(grams) and grams.most_common(1)[0][1] >= 5

    @torch.no_grad()
    def tr(texts, src, tgt, bs=32):
        tok.src_lang = src
        bos = tok.convert_tokens_to_ids(tgt)
        order = np.argsort([-len(t) for t in texts])
        out = [None] * len(texts)
        for s in range(0, len(texts), bs):
            idx = order[s:s + bs]
            enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True, truncation=True, max_length=256).to("cuda")
            max_new = min(400, int(enc["input_ids"].shape[1] * 3) + 16)
            gen = model.generate(**enc, forced_bos_token_id=bos, num_beams=4, max_new_tokens=max_new)
            n_hit[f"{src}->{tgt}"] += int(gen.shape[1] - 1 >= max_new)
            for i, t in zip(idx, tok.batch_decode(gen, skip_special_tokens=True)):
                out[i] = t.strip()
        if variant == "fixed":   # retry runaway repetitions once with an n-gram block
            for i, t in enumerate(out):
                if looped(t):
                    enc = tok([texts[i]], return_tensors="pt", truncation=True, max_length=256).to("cuda")
                    g = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(tgt), num_beams=4,
                                       no_repeat_ngram_size=3, max_new_tokens=min(400, int(enc["input_ids"].shape[1] * 3) + 16))
                    out[i] = tok.decode(g[0], skip_special_tokens=True).strip()
                    n_hit[f"retry {src}->{tgt}"] += 1
        return out

    rows = read_jsonl(CHUNKS)
    fixed = variant == "fixed"
    sents = [split_en(normalize_en(r["text"]) if fixed else r["text"], fixed) for r in rows]
    flat = [s for ss in sents for s in ss]
    lens = [len(ss) for ss in sents]

    def regroup(xs):
        it = iter(xs)
        return [[next(it) for _ in range(n)] for n in lens]

    for lk, (_, code) in LANGS.items():
        fwd = tr(flat, ENG, code)
        back = tr(fwd, code, ENG)
        for r, en_s, f_s, b_s in zip(rows, sents, regroup(fwd), regroup(back)):
            r.setdefault("sents_en", en_s)
            r[f"sents_{lk}"] = f_s
            r[f"sents_{lk}_back"] = b_s
            r[lk] = " ".join(f_s)
            r[f"{lk}_back"] = " ".join(b_s)
        print(f"{lk}: {len(flat)} sentences done", flush=True)
    path = trans_path(variant)
    write_jsonl(path, rows)
    print("hit max_new_tokens / retries:", dict(n_hit))
    print("wrote", path)


# ---------------------------------------------------------------- stage 3: score
def trans_path(variant):
    return TRANS if variant == "raw" else TRANS.replace(".jsonl", f"_{variant}.jsonl")


def numbers(s, lang=None):
    """Numbers as strings. Thousands separators dropped; Khmer/Lao digits mapped to ASCII.
    For Vietnamese, also return a locale-normalised version (0,5 -> 0.5 ; 1.000 -> 1000)."""
    s = s.translate(DIGITS)
    s = re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", s)            # 1 000
    raw = re.findall(r"\d+(?:[.,]\d+)*", s)
    def norm(x, decimal):
        th = "," if decimal == "." else "."
        x = re.sub(r"\%s(?=\d{3}(?!\d))" % th, "", x)                  # drop thousands separator
        return x.replace(decimal, ".")
    strict = [norm(x, ".") for x in raw]
    local = [norm(x, ",") for x in raw] if lang in ("vie", "khm", "lao") else strict   # all three use decimal comma (CLDR)
    return strict, local


def multiset_hits(ref, hyp):
    c = collections.Counter(hyp)
    hit = 0
    for x in ref:
        if c[x] > 0:
            c[x] -= 1
            hit += 1
    return hit


def latin_tokens(s):
    return re.findall(r"[A-Za-z][A-Za-z-]+", s)


def drug_found(drug, text, thr=0.8):
    """exact = drug spelled as in English; fuzzy = a Latin token within edit-similarity 0.8 (e.g. vi 'adrenalin')."""
    toks = [t.lower() for t in latin_tokens(text)]
    d = drug.lower()
    if d in toks or re.search(r"(?<![a-z])" + re.escape(d) + r"(?![a-z])", text.lower()):
        return "exact"
    if any(difflib.SequenceMatcher(None, d, t).ratio() >= thr for t in toks):
        return "fuzzy"
    return None


def units(s):
    return [UNIT_CANON[u.lower()] if u.lower() in UNIT_CANON else u for u in UNIT_RE.findall(s.translate(DIGITS))]


def score(variant="raw"):
    import sacrebleu
    rows = read_jsonl(trans_path(variant))
    if variant in ("fixed", "glossary", "protect"):   # post-processing: repair spaced-out decimals against the source
        for r in rows:
            for lk in LANGS:
                r[lk] = repair_decimals(r["text"], r[lk])
    report, per = {"model": MODEL_ID, "variant": variant, "n_chunks": len(rows), "langs": {}}, []
    for r in rows:
        per.append({"id": r["id"], "selected_for": r["selected_for"], "en": r["text"]})

    for lk, (lname, _) in LANGS.items():
        A = collections.Counter()
        fails = collections.defaultdict(list)
        for r, p in zip(rows, per):
            en, tg, bt = r["text"], r[lk], r[f"{lk}_back"]
            d = {"tgt": tg, "back": bt}
            # 1. numbers
            n_en, _ = numbers(en)
            n_tg_strict, n_tg_local = numbers(tg, lk)
            n_bt, _ = numbers(bt)
            h_s, h_l, h_b = multiset_hits(n_en, n_tg_strict), multiset_hits(n_en, n_tg_local), multiset_hits(n_en, n_bt)
            A["num_total"] += len(n_en); A["num_strict"] += h_s; A["num_locale"] += max(h_s, h_l); A["num_back"] += h_b
            extra = len(n_tg_strict) - h_s
            A["num_spurious"] += max(0, extra)
            d["numbers"] = {"en": n_en, "tgt": n_tg_strict, "back": n_bt, "ok_tgt": max(h_s, h_l) == len(n_en)}
            if max(h_s, h_l) < len(n_en):
                fails["numbers"].append(r["id"])
            # 2. negation
            neg_en = len(EN_NEG.findall(en))
            if neg_en:
                neg_tg = len(TGT_NEG[lk].findall(tg))
                neg_bt = len(EN_NEG.findall(bt)) + len(re.findall(r"\b(no|without|none)\b", bt, re.I))
                A["neg_chunks"] += 1; A["neg_cues_en"] += neg_en
                A["neg_present"] += neg_tg > 0
                A["neg_count_ok"] += neg_tg >= neg_en
                A["neg_back_present"] += neg_bt > 0
                A["neg_back_count_ok"] += neg_bt >= neg_en
                d["negation"] = {"en": neg_en, "tgt": neg_tg, "back": neg_bt}
                if neg_tg == 0:
                    fails["negation"].append(r["id"])
            # 3. drug names (each mention)
            drugs = [m.lower() for m in DRUG_RE.findall(en)]
            dd = []
            for dr in drugs:
                in_tg, in_bt = drug_found(dr, tg), drug_found(dr, bt)
                ok = in_tg is not None or in_bt is not None
                A["drug_total"] += 1; A["drug_exact"] += in_tg == "exact"; A["drug_latin"] += in_tg is not None
                A["drug_back"] += in_bt is not None; A["drug_ok"] += ok
                dd.append({"drug": dr, "tgt": in_tg, "back": in_bt})
                if not ok:
                    fails["drug"].append(f"{r['id']}:{dr}")
            d["drugs"] = dd
            # 4. units
            u_en, u_tg, u_bt = units(en), units(tg), units(bt)
            h_u = multiset_hits([u.lower() for u in u_en], [u.lower() for u in u_tg])
            A["unit_total"] += len(u_en); A["unit_ok"] += h_u
            A["unit_back"] += multiset_hits([u.lower() for u in u_en], [u.lower() for u in u_bt])
            d["units"] = {"en": u_en, "tgt": u_tg, "back": u_bt}
            if h_u < len(u_en):
                fails["units"].append(r["id"])
            # clinical terms in the back-translation
            for t, pat in CLIN_TERMS.items():
                k = len(re.findall(pat, en, re.I))
                if k:
                    got = min(k, len(re.findall(pat, bt, re.I)))
                    A["clin_total"] += k; A["clin_back"] += got
                    if got < k:
                        fails["clinical_term"].append(f"{r['id']}:{t}")
            # 5. sentence-level back-translation scores
            d["bt_bleu"] = sacrebleu.sentence_bleu(bt, [en]).score
            d["bt_chrf"] = sacrebleu.sentence_chrf(bt, [en], word_order=2).score
            # all safety-critical facts intact in the *translation*
            safe = (d["numbers"]["ok_tgt"] and ("negation" not in d or d["negation"]["tgt"] > 0)
                    and all(x["tgt"] or x["back"] for x in dd) and h_u == len(u_en))
            A["chunks_all_ok"] += safe
            d["all_ok"] = safe
            p[lk] = d
        hyp = [r[f"{lk}_back"] for r in rows]; ref = [r["text"] for r in rows]
        bleu = sacrebleu.corpus_bleu(hyp, [ref]).score
        chrf = sacrebleu.corpus_chrf(hyp, [ref], word_order=2).score
        report["langs"][lk] = {"name": lname, "counts": dict(A), "bt_BLEU": bleu, "bt_chrF++": chrf,
                               "failed_ids": {k: v for k, v in fails.items()}}
    json.dump(report, open(os.path.join(OUT, f"report_{variant}.json"), "w"), indent=1, ensure_ascii=False)
    write_jsonl(os.path.join(OUT, f"per_chunk_{variant}.jsonl"), per)

    # -------- console / markdown summary
    L = list(LANGS)
    def row(label, f):
        return f"| {label} | " + " | ".join(f(report['langs'][l]['counts'], report['langs'][l]) for l in L) + " |"
    frac = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "n/a"
    lines = ["| Check | " + " | ".join(LANGS[l][0] for l in L) + " |", "|---|" + "---|" * len(L),
             row("Numbers preserved, strict", lambda c, _: frac(c["num_strict"], c["num_total"])),
             row("Numbers preserved, locale-aware (0,5 = 0.5)", lambda c, _: frac(c["num_locale"], c["num_total"])),
             row("Spurious extra numbers in translation", lambda c, _: str(c["num_spurious"])),
             row("Negation present (chunks with EN negation)", lambda c, _: frac(c["neg_present"], c["neg_chunks"])),
             row("Negation count >= EN count", lambda c, _: frac(c["neg_count_ok"], c["neg_chunks"])),
             row("Drug names kept in Latin script, exact", lambda c, _: frac(c["drug_exact"], c["drug_total"])),
             row("Drug names Latin exact or close (>=0.8)", lambda c, _: frac(c["drug_latin"], c["drug_total"])),
             row("Drug names, Latin or recovered in back-translation", lambda c, _: frac(c["drug_ok"], c["drug_total"])),
             row("Units preserved", lambda c, _: frac(c["unit_ok"], c["unit_total"])),
             row("Back-translation BLEU", lambda _, R: f"{R['bt_BLEU']:.1f}"),
             row("Back-translation chrF++", lambda _, R: f"{R['bt_chrF++']:.1f}"),
             row("BT: numbers recovered", lambda c, _: frac(c["num_back"], c["num_total"])),
             row("BT: negation recovered", lambda c, _: frac(c["neg_back_present"], c["neg_chunks"])),
             row("BT: units recovered", lambda c, _: frac(c["unit_back"], c["unit_total"])),
             row("BT: clinical terms recovered (lower bound)", lambda c, _: frac(c["clin_back"], c["clin_total"])),
             row("**Chunks with ALL checks passing**", lambda c, _: frac(c["chunks_all_ok"], len(rows)))]
    md = "\n".join(lines)
    open(os.path.join(OUT, f"report_{variant}.md"), "w").write(md + "\n")
    print(md)
    for l in L:
        print(l, "failed:", report["langs"][l]["failed_ids"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--variant", default="raw", choices=["raw", "fixed", "glossary", "protect"],
                    help="fixed = dash normalisation + better sentence split + loop retry (translate) and decimal repair (score)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.select: select()
    if a.translate: translate(a.variant)
    if a.score: score(a.variant)
