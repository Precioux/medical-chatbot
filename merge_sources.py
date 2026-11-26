#!/usr/bin/env python
"""Part 2: merge mmore + Chandra + Docling + Qwen3-VL image descriptions into out/unified_output.jsonl.

    python merge_sources.py          # CPU only (login node, senv python: needs pymupdf), after describe_images.py

Per page (pages from mmore's paragraph_starts), walking the mmore text in order:
  - markdown tables in the mmore text  -> "table" blocks, paired in order with the Docling tables on that page
                                          (Docling grid in metadata.docling_grid; a Docling table with no mmore
                                          counterpart becomes its own block rendered from the grid)
  - the first <attachment> on a page   -> "algorithm" block from Chandra: only the parts of Chandra's page that
                                          mmore does not already have (token-coverage de-dup), <img> alts dropped
  - each <attachment>                  -> the page's next Qwen3-VL "image" block (Docling picture order);
                                          descriptions left over are appended at the end of the page
  - everything else                    -> "text" blocks, split at headings / ~1500 characters
Chapter/section come from the printed table of contents (PDF page = printed page + 13), each start page checked
against Docling section headers. On the page where a section starts, blocks before its heading stay in the
previous section.

Outputs: out/unified_output.jsonl, out/merge_report.json
"""
import collections, difflib, html, json, os, re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
MMORE = os.path.join(ROOT, "out", "mmore", "mmore_output.json")
CHANDRA = os.path.join(ROOT, "out", "chandra_pages.jsonl")
DOCLING = os.path.join(ROOT, "ocr", "output.json")
IMAGES = os.path.join(ROOT, "out", "image_descriptions.jsonl")
SKIPPED = os.path.join(ROOT, "out", "image_descriptions_skipped.jsonl")
OUT = os.path.join(ROOT, "out", "unified_output.jsonl")
REPORT = os.path.join(ROOT, "out", "merge_report.json")

PAGE_OFFSET = 13          # PDF page = printed page + 13 (checked: Chapter I printed 3 -> PDF 16; Chapter II 271 -> 284)
MAX_TEXT = 1500           # chars per text block
DEDUP_COVERAGE = 0.6      # a Chandra block is "new" if < 60% of its words already occur on the mmore page

# Table of contents (Chandra page 9 + Docling page 10; printed page numbers)
CHAPTERS = [("Front matter", None), ("I - Emergency", 3), ("II - Cardiology", 271)]
TOC = [(1, "Assessment the Patients in Emergency Room", 4), (2, "Oxygen Therapy and Respiratory Supports", 17),
       (3, "Early Warning Score in Hospital", 29), (4, "Shock", 36), (5, "Hemorrhagic Shock", 50),
       (6, "Stroke Syndrome in Emergency", 63), (7, "Coma", 76), (8, "Allergic Reaction", 86),
       (9, "General Management of Poisoning", 95), (10, "Paracetamol Poisoning", 107),
       (11, "Methamphetamines Poisoning", 116), (12, "Organophosphate and Carbamate Insecticides Poisoning", 123),
       (13, "Methanol and Ethylene Glycol Intoxication", 132),
       (14, "Cardiopulmonary Arrest Basic and Advance Cardiac Life Support", 141),
       (15, "Acute Metabolic Complication of Diabetes Mellitus, Hyperosmolar Hyperglycemia State", 159),
       (16, "Traumatism in Adult", 167), (17, "Initial Management of Head Trauma", 177),
       (18, "Initial Management of Chest Trauma", 184), (19, "Acute Abdominal Syndrome", 193),
       (20, "Hyperkalemia", 202), (21, "Hypokalemia", 210), (22, "Hypernatremia", 219), (23, "Hyponatremia", 228),
       (24, "Sepsis and Septic Shock, Empirical Antibiotherapy", 236),
       (25, "Severe Acute Respiratory Infection (SARI) and Influenza", 244), (26, "Snake Bites", 253),
       (27, "Massive Blood Transfusion", 263),
       (28, "Acute Coronary Syndrome ST-Elevation Myocardial Infarction (STEMI)", 272),
       (29, "Acute Coronary Syndrome Non-ST Elevation Myocardial Infarction (NSTEMI)", 280),
       (30, "Chronic Coronary Syndrome", 289), (31, "Emergency Tachy-Arrhythmia", 293),
       (32, "Emergency Bradycardia", 302), (33, "Pulmonary Embolism", 306), (34, "Acute Pulmonary Edema", 313),
       (35, "Hypertension", 320), (36, "Chronic Heart Failure", 332), (37, "Aortic Regurgitation (AR)", 346),
       (38, "Aortic Stenosis (AS)", 353), (39, "Management of Aortic Aneurysm", 359),
       (40, "Mitral Regurgitation (MR)", 364), (41, "Mitral Stenosis (MS)", 371),
       (42, "Management and Surveillance of Prosthetic Valves", 379), (43, "Deep Venous Thrombosis", 384),
       (44, "Prevention of Deep Venous Thrombosis", 390), (45, "Infectious Endocarditis", 394),
       (46, "Infectious Endocarditis", 404), (47, "Pericarditis", 415), (48, "Constrictive Pericarditis", 419),
       (49, "Management of Cardiovascular Diseases During Pregnancy", 428),
       (50, "Cardiovascular Drugs and Pregnancy", 451),
       (51, "Cardiac Evaluation before Non-Cardiac Surgery (NCS)", 456)]


# ---------------------------------------------------------------- helpers
def words(s):
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", s.lower())


class TopLevel(HTMLParser):
    """Split an HTML fragment into its top-level elements (raw HTML strings)."""
    VOID = {"br", "img", "hr", "input", "meta", "link"}

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src, self.depth, self.blocks, self.start = src, 0, [], None
        self.lines = [0]
        for line in src.splitlines(keepends=True):
            self.lines.append(self.lines[-1] + len(line))
        self.feed(src)
        self.close()
        if self.start is not None:
            self.blocks.append(src[self.start:])

    def pos(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            if self.depth == 0:
                self.blocks.append(self.get_starttag_text())
            return
        if self.depth == 0:
            self.start = self.pos()
        self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        self.depth = max(0, self.depth - 1)
        if self.depth == 0 and self.start is not None:
            end = self.src.find(">", self.pos()) + 1
            self.blocks.append(self.src[self.start:end])
            self.start = None

    def handle_data(self, data):
        if self.depth == 0 and data.strip():
            self.blocks.append(data)


def html_to_text(h):
    """Chandra HTML -> readable markdown-ish text (lists, line breaks, table rows as ' | ')."""
    h = re.sub(r"<img[^>]*>", "", h)
    h = re.sub(r"<sub>(.*?)</sub>|<sup>(.*?)</sup>", lambda m: m.group(1) or m.group(2), h)
    h = re.sub(r"(?<=[\d.]-)\s*<br\s*/?>\s*(?=[\d.])", "", h)                  # '0.3-<br/>0.5mg' is one dose range
    h = re.sub(r"<t([dh])([^>]*)>(.*?)</t\1>",                                # line breaks inside a cell -> '; '
               lambda m: f"<t{m.group(1)}{m.group(2)}>" + re.sub(r"\s*<br\s*/?>\s*", "; ", m.group(3)).strip("; ") + f"</t{m.group(1)}>",
               h, flags=re.S)
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"<li[^>]*>", "\n- ", h)
    h = re.sub(r"</t[dh]>\s*<t[dh][^>]*>", " | ", h)
    h = re.sub(r"<tr[^>]*>", "\n| ", h)
    h = re.sub(r"</tr>", " |", h)
    h = re.sub(r"<h(\d)[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", h)
    h = re.sub(r"</(p|div|h\d|ul|ol|table)>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    h = re.sub(r"(\n\| )\s*\n\s*", r"\1", h)                            # no newline right after a row's opening '| '
    h = re.sub(r"([,;:])\s*;", r"\1", h)
    h = re.sub(r"\s*\n\s*\|[ \t]*(?=\n|$)", " |", h)                          # row-closing '|' on its own line
    h = re.sub(r"[ \t]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n\n", h).strip()


LATEX = {r"\geq": "≥", r"\ge": "≥", r"\leq": "≤", r"\le": "≤", r"\neq": "≠", r"\times": "×", r"\circ": "◦",
         r"\sim": "~", r"\approx": "≈", r"\pm": "±", r"\min": "min", r"\beta": "β", r"\alpha": "α", r"\mu": "µ",
         r"\nu": "ν", r"\%": "%"}


def unlatex(s):
    """mmore writes some formulas as inline LaTeX ('pH $\\geq$ 7.30', '$> 50 \\times 10^9/L$'). Plain text is safer for
    chunking and translation: map the commands to Unicode, unwrap \\text{..}, drop the $ delimiters."""
    s = re.sub(r"\\n(?=[a-z])", " ", s)                                      # literal backslash-n left by mmore
    def one(m):
        t = m.group(1)
        t = re.sub(r"\\(?:text|mathrm|textsc|textbf|mathbf|operatorname)\s*\{([^{}]*)\}", r"\1", t)
        for k in sorted(LATEX, key=len, reverse=True):
            t = re.sub(re.escape(k) + r"(?![a-zA-Z])", LATEX[k], t)
        t = re.sub(r"\^\{?([+-])\}?", r"\1", t)                               # K^+ -> K+
        t = re.sub(r"\^\{([^{}]*)\}", r"^\1", t)                              # 10^{9} -> 10^9
        return re.sub(r"\s+", " ", t).strip()
    s = re.sub(r"\$([^$\n]{1,200})\$", lambda m: one(m), s)
    for k in sorted(LATEX, key=len, reverse=True):                           # stray commands outside $...$
        s = re.sub(re.escape(k) + r"(?![a-zA-Z])", LATEX[k], s)
    return s


# ---------------------------------------------------------------- repairs from the PDF text layer
# The PDF (Word export) has a real text layer. mmore sometimes drops a range dash ('3 - 6 months' -> '3 6 months'),
# turns '>' into '≥', or loses the exponent of 10⁹/L. Each repair below is applied only when that page's own
# text layer proves it (the corrected form occurs on the page and the wrong form does not).
_DASH = re.compile(r"[\u2010-\u2015\u2212]")


def page_ref(doc, page):
    import unicodedata
    t = unicodedata.normalize("NFKC", doc[page - 1].get_text("text", sort=True))
    return re.sub(r"\s+", " ", _DASH.sub("-", t))


def repair(content, ref, log):
    num = r"\d+(?:\.\d+)?"
    # 1. dropped range dash: 'a b' in output, 'a - b' in the PDF page, and 'a b' not in the PDF page
    for a_, b_ in set(re.findall(rf"(?<![\d.])({num})\s*-\s*({num})(?![\d.])", ref)):
        bad = rf"(?<![\d.\-])({re.escape(a_)})[ \t]+({re.escape(b_)})(?![\d.])"
        if re.search(bad, content) and not re.search(bad, ref):
            content, n = re.subn(bad, lambda m: m.group(1) + "-" + m.group(2), content)
            log["range_dash_restored"] += n
    # 2. comparator changed: PDF has '>X' but not '≥X'; output has '≥ X' (and vice versa, and < / ≤)
    for sign, wrong in ((">", "≥"), ("<", "≤"), ("≥", ">"), ("≤", "<")):
        for x in set(re.findall(rf"{re.escape(sign)}\s*({num})", ref)):
            if re.search(rf"{re.escape(wrong)}\s*{re.escape(x)}(?![\d.])", ref):
                continue
            content, n = re.subn(rf"{re.escape(wrong)}(\s*){re.escape(x)}(?![\d.])",
                                 lambda m, s=sign, v=x: s + m.group(1) + v, content)
            log["comparator_restored"] += n
    # 3. lost exponent: PDF '× 109/L' (10⁹ flattened by the text layer), output '× 10 /L'
    if re.search(r"×\s*10\s*9\s*/\s*L", ref):
        content, n = re.subn(r"×(\s*)10(?:\s|<br\s*/?>)+/\s*L", lambda m: "×" + m.group(1) + "10^9/L", content)
        log["exponent_restored"] += n
    return content


def grid_markdown(t):
    d = t["data"]
    g = [["" for _ in range(d["num_cols"])] for _ in range(d["num_rows"])]
    for c in d["table_cells"]:
        g[c["start_row_offset_idx"]][c["start_col_offset_idx"]] = c["text"].replace("|", "/").replace("\n", " ")
    lines = ["| " + " | ".join(r) + " |" for r in g]
    if lines:
        lines.insert(1, "|" + "---|" * d["num_cols"])
    return "\n".join(lines)


def grid_meta(t):
    d = t["data"]
    return {"num_rows": d["num_rows"], "num_cols": d["num_cols"], "label": t["label"], "ref": t["self_ref"],
            "bbox": t["prov"][0]["bbox"],
            "cells": [{"row": c["start_row_offset_idx"], "col": c["start_col_offset_idx"],
                       "row_span": c["row_span"], "col_span": c["col_span"], "text": c["text"],
                       "header": bool(c.get("column_header") or c.get("row_header"))} for c in d["table_cells"]]}


def split_text(t):
    """Text -> blocks at markdown headings, then packed paragraphs up to MAX_TEXT chars."""
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", t):
        para = para.strip()
        if not para:
            continue
        if (para.startswith("#") and cur) or len(cur) + len(para) > MAX_TEXT:
            if cur:
                out.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- sections
def section_starts(docling):
    """[(pdf_page, chapter, section_number, title, verified)] using the TOC, checked against Docling headers."""
    heads = [(t["prov"][0]["page_no"], t["text"]) for t in docling["texts"]
             if t["label"] == "section_header" and t.get("prov")]
    out = []
    for name, printed in CHAPTERS[1:]:
        out.append((printed + PAGE_OFFSET, name, None, None, True))
    for num, title, printed in TOC:
        exp = printed + PAGE_OFFSET
        key = re.sub(r"[^a-z]", "", title.lower())[:22]
        found = None
        for dp in (0, 1, -1, 2, 3, -2):                   # nearest header page whose text matches the title
            for p, h in heads:
                hk = re.sub(r"[^a-z]", "", h.lower())
                if p == exp + dp and len(hk) >= 6 and (difflib.SequenceMatcher(None, key, hk[:len(key)]).ratio() > 0.8):
                    found = p
                    break
            if found:
                break
        chap = CHAPTERS[1][0] if num <= 27 else CHAPTERS[2][0]
        out.append((found or exp, chap, num, title, found is not None))
    return sorted(out, key=lambda x: (x[0], x[2] is not None))


def locate(starts, page):
    """(chapter, section, number) in force at the top of `page`, plus the section starting on it (if any)."""
    chap, sec, num = CHAPTERS[0][0], "Front matter", None
    starting = []
    for p, c, n, t, _ in starts:
        if p < page:
            chap = c
            if n is not None:
                sec, num = t, n
            else:
                sec, num = f"Chapter {c.split(' - ')[0]} introduction", None
        elif p == page:
            starting.append((c, n, t))
    return (chap, sec, num), starting


# ---------------------------------------------------------------- main
def main():
    mm = json.load(open(MMORE))
    T = mm["text"]
    starts = {}
    for off, pg, _ in mm["metadata"]["paragraph_starts"]:
        if pg >= 1:
            starts.setdefault(pg, off)
    pages = sorted(starts)
    page_text = {p: T[starts[p]:(starts[pages[i + 1]] if i + 1 < len(pages) else len(T))] for i, p in enumerate(pages)}
    chandra = {json.loads(l)["page"]: json.loads(l)["content"] for l in open(CHANDRA)}
    doc = json.load(open(DOCLING))
    tables = collections.defaultdict(list)
    for t in doc["tables"]:
        if t.get("prov"):
            tables[t["prov"][0]["page_no"]].append(t)
    imgs = collections.defaultdict(list)
    if os.path.exists(IMAGES):
        for l in open(IMAGES):
            r = json.loads(l)
            imgs[r["page"]].append(r)
    ref_order = {p["self_ref"]: i for i, p in enumerate(doc["pictures"])}
    for p in imgs:
        imgs[p].sort(key=lambda r: ref_order.get(r["picture_ref"], 0))
    n_skipped = collections.Counter(json.loads(l).get("reason") for l in open(SKIPPED)) if os.path.exists(SKIPPED) else {}

    sec_starts = section_starts(doc)
    blocks, stats = [], collections.Counter()
    gaps, unmatched_imgs = [], []

    for page in pages:
        (chap, sec, num), starting = locate(sec_starts, page)
        txt = page_text[page]
        # section change inside the page: find the heading of the first section starting here
        split_at = None
        if starting:
            c, n, t = starting[-1]
            if n is not None:
                key = re.escape(t.split(",")[0].split("(")[0].strip()[:20]).replace(r"\ ", r"\s+")
                m = re.search(key, txt, re.I)
            else:
                m = re.search(r"CHAPTER\s+" + c.split(" - ")[0] + r"\b", txt, re.I)
            split_at = txt.rfind("\n", 0, m.start()) + 1 if m else 0      # start of the heading's line
            new_sec = (c, t if n is not None else f"Chapter {c.split(' - ')[0]} introduction", n)

        page_blocks = []

        def add(btype, source, content, pos, **meta):
            if not content or not content.strip():
                return
            s = (chap, sec, num)
            if split_at is not None and pos >= split_at:
                s = new_sec
            page_blocks.append({"page": page, "type": btype, "source": source, "chapter": s[0], "section": s[1],
                                "section_number": s[2], "content": content.strip(),
                                "metadata": {k: v for k, v in meta.items() if v is not None}})

        # walk the mmore text: tables and attachments are cut out in order
        pieces = re.split(r"(<attachment>|(?:^\|.*\|[ \t]*(?:\n|$))+)", txt, flags=re.M)
        pos, dl_tables, page_imgs, att_seen = 0, list(tables.get(page, [])), list(imgs.get(page, [])), 0
        for piece in pieces:
            if piece is None:
                continue
            if piece == "<attachment>":
                if att_seen == 0 and page in chandra:
                    new = []
                    mm_words = set(words(txt))
                    for b in TopLevel(chandra[page]).blocks:
                        if b.lstrip().startswith("<img"):
                            continue
                        bt = html_to_text(b)
                        w = words(bt)
                        if not w:
                            continue
                        cov = sum(x in mm_words for x in w) / len(w)
                        if cov < DEDUP_COVERAGE:
                            new.append(bt)
                    if new:
                        add("algorithm", "chandra", "\n\n".join(new), pos)
                    else:
                        stats["attachment_pages_chandra_nothing_new"] += 1
                if page_imgs:
                    r = page_imgs.pop(0)
                    add("image", "qwen3", r["description"], pos, bbox=r["bbox"], image_path=r["image_path"],
                        image_type=r["type"], picture_ref=r["picture_ref"])
                att_seen += 1
            elif piece.lstrip().startswith("|"):
                t = dl_tables.pop(0) if dl_tables else None
                add("table", "mmore" if t is None else "mmore+docling", piece, pos,
                    docling_grid=grid_meta(t) if t else None)
            else:
                for chunk in split_text(piece):
                    add("text", "mmore", chunk, pos + max(0, piece.find(chunk[:40])))
            pos += len(piece)
        for t in dl_tables:                       # Docling tables mmore did not render as markdown
            add("table", "docling", grid_markdown(t), pos, docling_grid=grid_meta(t))
            stats["docling_only_tables"] += 1
        for r in page_imgs:                       # descriptions without a matching <attachment>
            add("image", "qwen3", r["description"], pos, bbox=r["bbox"], image_path=r["image_path"],
                image_type=r["type"], picture_ref=r["picture_ref"])
            unmatched_imgs.append(r["picture_ref"])
        if not page_blocks:
            gaps.append(page)
        blocks += page_blocks

    import pymupdf
    pdf = pymupdf.open(os.path.join(ROOT, "data", "source.pdf"))
    refs = {}
    for i, b in enumerate(blocks):
        b["id"] = f"chunk_{i:05d}"
        # a line break inside a numeric range ('1 -<br>5L/min', '0.23 -\n0.35') -> one range
        b["content"] = re.sub(r"(?<=\d)(\s*[-\u2013]\s*)(?:<br\s*/?>|\n)\s*(?=\d)", r"\1", b["content"])
        b["content"] = unlatex(b["content"])
        if b["source"] in ("mmore", "mmore+docling"):     # only text that came from mmore; figures are not in the layer
            if b["page"] not in refs:
                refs[b["page"]] = page_ref(pdf, b["page"])
            before = b["content"]
            b["content"] = repair(b["content"], refs[b["page"]], stats)
            if b["content"] != before:
                b.setdefault("metadata", {})["repaired_from_pdf_text_layer"] = True
        # mmore sometimes opens a markdown link inside a number ('56(4):5[49-563. \\[PubMed\\]](url)')
        b["content"] = re.sub(r"(?<=\d)\[(?=\d)", "", b["content"])
    order = ["id", "page", "type", "source", "chapter", "section", "section_number", "content", "metadata"]
    with open(OUT, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps({k: b[k] for k in order}, ensure_ascii=False) + "\n")

    per_sec = collections.Counter(f"{b['section_number'] or '-'} {b['section']}" for b in blocks)
    covered = sorted({b["section_number"] for b in blocks if b["section_number"]})
    report = {
        "total_blocks": len(blocks),
        "blocks_per_type": dict(collections.Counter(b["type"] for b in blocks)),
        "blocks_per_source": dict(collections.Counter(b["source"] for b in blocks)),
        "blocks_per_section": dict(sorted(per_sec.items(), key=lambda kv: (kv[0].split()[0] == "-",
                                                                            int(kv[0].split()[0]) if kv[0].split()[0].isdigit() else 0))),
        "pages_total": len(pages),
        "pages_with_no_content": gaps,
        "sections_covered": f"{len(covered)}/{len(TOC)}",
        "sections_missing": [n for n, _, _ in TOC if n not in covered],
        "section_starts": [{"pdf_page": p, "chapter": c, "number": n, "title": t, "verified_by_docling_header": v}
                           for p, c, n, t, v in sec_starts],
        "images_described": sum(len(v) for v in imgs.values()),
        "images_skipped": dict(n_skipped),
        "images_without_attachment_marker": unmatched_imgs,
        "notes": dict(stats),
    }
    json.dump(report, open(REPORT, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: report[k] for k in ["total_blocks", "blocks_per_type", "blocks_per_source", "sections_covered",
                                             "images_described", "images_skipped", "notes"]}, indent=1))
    print("pages with no content:", gaps)
    print("unverified section starts:", [(n, t, p) for p, c, n, t, v in sec_starts if not v])
    print("wrote", OUT, "and", REPORT)


if __name__ == "__main__":
    main()
