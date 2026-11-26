"""Build data/medical_glossary.json from the OCR'd glossaries + Wikidata.

    python build_glossary.py --lao         # parse MOH English-Lao glossary (Tesseract text, Chandra cross-check)
    python build_glossary.py --vi          # Wikidata Vietnamese (+Khmer/Lao if present) labels for the English terms
    python build_glossary.py --merge       # -> data/medical_glossary.json

Every entry carries its source and "reviewed": false. Lao entries carry an OCR-agreement score:
Tesseract (lao+eng) and Chandra read the same printed entry independently; when both give the same Lao
string the entry is much more likely to be right. Nothing here has been checked by a native speaker.
"""
import os, re, sys, json, html, difflib, argparse, unicodedata, urllib.request, urllib.parse, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OCR = os.path.join(ROOT, "out", "glossary_ocr")
WORK = os.path.join(ROOT, "out", "glossary_build")
GLOSSARY = os.path.join(ROOT, "data", "medical_glossary.json")
LAO_PAGES = range(23, 90)          # English-Lao section of B01577.pdf (0-based PDF pages)
LAO_SRC = "MOH Lao PDR, English-Lao Medical Glossary (B01577), OCR"

LAO = re.compile(r"[຀-໿]")
THAI = re.compile(r"[฀-๿]")
POS = {"n", "v", "a", "an", "a,n", "adj", "adv", "pl", "prefix", "suffix", "n pl"}


def norm_lao(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace("ໍາ", "ຳ").replace("າໍ", "ຳ")   # ໍ + າ  ->  ຳ  (sara am)
    s = re.sub(r"\s+", " ", s).strip(" ,;.")
    return s


def split_head(left):
    """'large intestine n' / 'laryngitis ກ' / 'bath ๓' -> 'large intestine' (drop the POS token, often garbled)."""
    toks = left.split()
    while toks and (toks[-1].lower() in POS or not re.fullmatch(r"[A-Za-z][A-Za-z'’()\-]*", toks[-1]) or len(toks[-1]) == 1):
        toks.pop()
    en = " ".join(toks)
    return en if re.fullmatch(r"[A-Za-z][A-Za-z'’()\- ]*", en or "") else None


def parse_lines(lines):
    """Glossary lines -> entries {en, lo}, xrefs {en: target}, synonyms {en: head}."""
    entries, xrefs, syn = [], {}, {}
    last, can_continue = None, False
    for raw in lines:
        line = raw.strip()
        if not line or "Medical Glossary" in line or "ຄຳສັບການແພດ" in line:
            can_continue = False
            continue
        m = re.match(r"^(.*?)\b(?:see|SEE)\b\s+([A-Za-z][A-Za-z'’\- ]*?)(?:\s+(?:n|v|a|an|adj|pl)\b.*)?$", line)
        if m and len(LAO.findall(m.group(1))) <= 1 and split_head(LAO.sub(" ", m.group(1))) and not re.match(r"(?i)\s*(also|compare)\b", line):
            xrefs[split_head(LAO.sub(" ", m.group(1))).lower()] = m.group(2).strip().lower()
            can_continue = False
            continue
        am = re.match(r"(?i)^also\s+(.+)$", line)
        if am and last is not None:
            for part in am.group(1).split(","):
                h = split_head(part.strip())
                if h:
                    syn[h.lower()] = last["en"]
            can_continue = False
            continue
        k = LAO.search(line)
        if k and not THAI.search(line):
            left, right = line[:k.start()], line[k.start():]
            h = split_head(left) if re.search(r"[A-Za-z]{2,}", left) else None
            if h:
                last = {"en": h, "lo": right}
                entries.append(last)
                can_continue = True
                continue
            if can_continue and not re.search(r"[A-Za-z]", line) and last is not None:
                last["lo"] += " " + line            # wrapped Lao gloss
                continue
        can_continue = False
    keep = []
    for e in entries:
        e["lo"] = norm_lao(re.sub(r"^[\u0E80-\u0EFF]\s+", "", e["lo"]))
        sm = re.match(r"(?i)^(.*?)\s+see\s+([A-Za-z][A-Za-z'’\- ]*)$", e["en"])
        if sm:                                   # 'bath v see bathe' + misread POS letter -> cross-ref
            h = split_head(sm.group(1))
            if h:
                xrefs.setdefault(h.lower(), split_head(sm.group(2)) or sm.group(2).strip().lower())
            continue
        if e["en"].lower().startswith("also") or len(LAO.findall(e["lo"])) < 3:
            continue
        keep.append(e)
    entries = keep
    return entries, xrefs, syn


def chandra_lines(content):
    c = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>|</tr>|</td>", "\n", content)
    c = html.unescape(re.sub(r"<[^>]+>", "", c))
    return c.splitlines()


def build_lao():
    tess, chan = [], []
    xrefs, syn = {}, {}
    chandra = {json.loads(l)["page"]: json.loads(l)["content"] for l in open(os.path.join(OCR, "lao_pages.jsonl"))}
    for p in LAO_PAGES:
        t = open(os.path.join(OCR, f"tess_lao-eng_p{p:03d}.txt"), encoding="utf-8").read().splitlines()
        e, x, s = parse_lines(t)
        for d in e: d["page"] = p
        tess += e; xrefs.update(x); syn.update(s)
        e2, x2, s2 = parse_lines(chandra_lines(chandra[p]))
        for d in e2: d["page"] = p
        chan += e2
        for k, v in x2.items(): xrefs.setdefault(k, v)
        for k, v in s2.items(): syn.setdefault(k, v)
    # cross-check: for each Tesseract entry, best Chandra reading of the same headword on the same/adjacent page
    by_head = {}
    for c in chan:
        by_head.setdefault(c["en"].lower(), []).append(c)
    out = []
    for e in tess:
        cands = [c for c in by_head.get(e["en"].lower(), []) if abs(c["page"] - e["page"]) <= 1]
        best = max(cands, key=lambda c: difflib.SequenceMatcher(None, e["lo"], c["lo"]).ratio(), default=None)
        r = difflib.SequenceMatcher(None, e["lo"], best["lo"]).ratio() if best else None
        out.append({"en": e["en"], "lo": e["lo"], "lo_chandra": best["lo"] if best else None,
                    "ocr_agreement": round(r, 3) if r is not None else None, "page": e["page"]})
    # headwords Chandra found but Tesseract missed: keep, flagged single-OCR
    seen = {e["en"].lower() for e in out}
    for c in chan:
        if c["en"].lower() not in seen:
            out.append({"en": c["en"], "lo": c["lo"], "lo_chandra": c["lo"], "ocr_agreement": None,
                        "page": c["page"], "chandra_only": True})
            seen.add(c["en"].lower())
    os.makedirs(WORK, exist_ok=True)
    json.dump({"entries": out, "xrefs": xrefs, "synonyms": syn},
              open(os.path.join(WORK, "lao.json"), "w"), ensure_ascii=False, indent=0)
    ag = [e["ocr_agreement"] for e in out if e["ocr_agreement"] is not None]
    print(f"Lao: {len(out)} entries ({sum(1 for e in out if e.get('chandra_only'))} Chandra-only), "
          f"{len(xrefs)} see-refs, {len(syn)} ALSO-synonyms; cross-checked {len(ag)}: "
          f"agree>=0.9 {sum(a >= 0.9 for a in ag)}, 0.6-0.9 {sum(0.6 <= a < 0.9 for a in ag)}, <0.6 {sum(a < 0.6 for a in ag)}")


# ---------------------------------------------------------------- merge
# Lao: never auto-apply everyday / polysemous headwords (wrong sense is worse than no glossary).
LAO_BLOCK = set("""stroke shock depression flush host state stage period chart control test help treat treatment patient
doctor hospital normal cause body head internal outer medical mental risk tube weight aspect assistance excited
female sensitivity dangerous urgent disability distress drug organ syndrome therapy prevention consultation
obstruction occlusion acute fluid oral
check time side system condition increase sign loss rest hole person think connect connection function energy
strength external cold hot heat burn broken calm relax application apply ability dress fast sense stability tension
voice vision damage critical crisis ache lens cortex ventricle giardia trichomoniasis sclerosis bubonic plague
male sex mankind born die dead death lump scratch hear hearing eye face nose limb arm side medicine""".split())
# Vietnamese Wikidata labels that are the wrong sense for clinical text (checked by hand, 2026-11-25)
VI_REJECT = {"infusion": "herbal infusion (tea)", "weaning": "weaning a baby from breastfeeding",
             "oxygen saturation": "dissolved oxygen", "glomerular filtration rate": "kidney function",
             "infant": "label means newborn"}
# guideline surface forms -> Wikidata concept label
VI_ALIASES = {"blood transfusion": ["transfusion", "transfusions"], "contraindication": ["contraindications"],
              "blood glucose": ["plasma glucose", "serum glucose"], "intramuscular injection": [],
              "epileptic seizure": []}


def first_sense(s):
    s = re.split(r"[,;]", s or "")[0]
    return re.sub(r"\s+", "", s)


def merge():
    lao = json.load(open(os.path.join(WORK, "lao.json")))
    wd = json.load(open(os.path.join(WORK, "wikidata.json")))["chosen"]
    G = {}
    for e in lao["entries"]:
        k = e["en"].lower()
        if k in G:                      # keep first sense block of a headword (noun usually first)
            continue
        fs_t, fs_c = first_sense(e["lo"]), first_sense(e.get("lo_chandra"))
        use = bool(fs_t) and fs_t == fs_c and not e.get("chandra_only") and k not in LAO_BLOCK
        G[k] = {"en": e["en"], "km": None, "lo": re.sub(r"\s+", "", re.split(r"[,;]", e["lo"])[0]), "lo_full": e["lo"], "vi": None,
                "src": {"lo": f"{LAO_SRC} p{e['page']}; tess/chandra agreement {e['ocr_agreement']}"},
                "use": {"lo": use}, "reviewed": False}
    for t, v in wd.items():
        if not v:
            continue
        label = re.sub(r"\s*\(.*?\)\s*$", "", v["vi"]).strip()
        for form in [t] + VI_ALIASES.get(t, []):
            g = G.setdefault(form, {"en": form, "km": None, "lo": None, "vi": None, "src": {}, "use": {}, "reviewed": False})
            g["vi"] = label
            g["src"]["vi"] = f"Wikidata {v['item']}" + ("" if v["medical"] else " (no MeSH/ICD id)")
            g["use"]["vi"] = v["medical"] and t not in VI_REJECT
            if t in VI_REJECT:
                g["src"]["vi"] += f"; REJECTED: {VI_REJECT[t]}"
            if v.get("km"):
                g["km"] = v["km"]; g["src"]["km"] = f"Wikidata {v['item']}"; g["use"]["km"] = False
    out = sorted(G.values(), key=lambda g: g["en"].lower())
    os.makedirs(os.path.dirname(GLOSSARY), exist_ok=True)
    json.dump(out, open(GLOSSARY, "w"), ensure_ascii=False, indent=1)
    for l in ["km", "lo", "vi"]:
        print(f"{l}: {sum(1 for g in out if g[l])} entries, {sum(1 for g in out if g['use'].get(l))} auto-applied")
    print("wrote", GLOSSARY)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lao", action="store_true")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    if a.merge:
        merge()
    if a.lao:
        build_lao()
