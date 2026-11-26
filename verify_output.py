#!/usr/bin/env python
"""Completeness check of out/unified_output.jsonl against the PDF's own text layer.

    python verify_output.py        # CPU, login node; ~1 min

The PDF is a Word 2019 export with a real text layer (embedded Calibri/Times/Arial). Text drawn as images
(scanned flowcharts, photos) is not in it, so those pages can only be checked for what the layer does contain.
pdftotext is not installed on the login node; PyMuPDF's get_text(sort=True) reads the same layer.

Checks
 1  word coverage per page: lowercase words of 3+ letters in the PDF text that occur in the page's blocks
 2  number coverage per page: numbers incl. decimals, ranges and comparison signs; "exact" = same token after
    normalising dashes and <=/>=; "value" = every bare number of the token present. Missing = not found by value.
    The printed page number (PDF page - 13) is excluded.
 3  figure accounting: each of the 184 Docling pictures is exactly one of described / DECORATIVE / skipped-small
 4  leftovers: <attachment> markers, empty / <5-char blocks, repeated-word loops
 5  out/review.html: 20 pages (page image | extracted blocks, missing numbers in red)
Outputs: out/completeness_report.json, out/review.html
"""
import base64, collections, html, io, json, os, random, re, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(ROOT, "data", "source.pdf")
UNIFIED = os.path.join(ROOT, "out", "unified_output.jsonl")
DOCLING = os.path.join(ROOT, "ocr", "output.json")
DESC = os.path.join(ROOT, "out", "image_descriptions.jsonl")
SKIP = os.path.join(ROOT, "out", "image_descriptions_skipped.jsonl")
PAGES = os.path.join(ROOT, "pages")
REPORT = os.path.join(ROOT, "out", "completeness_report.json")
REVIEW = os.path.join(ROOT, "out", "review.html")
PAGE_OFFSET = 13
WORD_FLAG = 0.90
FORCED = [43, 59, 229, 273, 338]

KM_LO_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩໐໑໒໓໔໕໖໗໘໙", "01234567890123456789")
DASH = re.compile(r"[‐-―−]")
NUM = re.compile(r"(?:[≤≥<>]=?\s*)?\d+(?:[.,]\d+)*(?:\s*-\s*\d+(?:[.,]\d+)*)?")


def norm_text(s):
    """Both sides: NFKC (10⁹ -> 109, m² -> m2, 𝑚 -> m), <sup>/<sub>/<br> tags dropped, unified dashes and signs."""
    s = unicodedata.normalize("NFKC", html.unescape(s)).translate(KM_LO_DIGITS)   # ២០២៥ -> 2025 (stage-1 MT)
    s = re.sub(r"</?(?:sup|sub)>", "", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = s.replace("\\times", "×").replace("$", "")                       # LaTeX: $> 50 \times 10^9/L$
    s = re.sub(r"\b10\s*\^?\s*\{?(\d{1,2})\}?\s*/\s*([a-zA-Z])", r"10\1/\2", s)   # 10^9/L, 10 9 /L -> 109/L
    s = re.sub(r"(?<=[x×])\s*10\s*\^?\s*(\d)\b", r"10\1", s)                    # 50x10 9 -> 50x109
    s = DASH.sub("-", s)
    s = re.sub(r"(?<=\d)\^(?=\d)", "", s)            # build_unified writes superscripts as 10^9, 2030^1
    s = s.replace("<=", "≤").replace(">=", "≥").replace("=<", "≤").replace("=>", "≥")
    s = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)            # 1,000 -> 1000
    return s


def numbers(s):
    """Normalised number tokens: '≤91', '9-11', '0.5', '30-35'."""
    return [re.sub(r"\s+", "", m) for m in NUM.findall(norm_text(s))]


def bare(tok):
    return re.findall(r"\d+(?:[.,]\d+)*", tok)


def words(s):
    return re.findall(r"[a-z]{3,}", s.lower())


def loop_score(s):
    """Longest run of an immediately repeated 1-3 word unit (e.g. 'renal failure, renal failure, ...')."""
    w = re.findall(r"\w+", s.lower())
    best = 1
    for n in (1, 2, 3):
        run = 1
        for i in range(n, len(w) - n + 1, n):
            if w[i:i + n] == w[i - n:i]:
                run += 1
                best = max(best, run)
            else:
                run = 1
    return best


SYMBOLS = "μ≤≥↑↓×÷β∼≈±→←°"


def margin_numbers(page):
    """Pure-number lines in the top/bottom 8% of the page: page numbers (dropped by build_unified as well).
    Includes wrongly printed ones, e.g. '288' on PDF page 284 (should be 271)."""
    H, out = page.rect.height, []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if re.fullmatch(r"\d{1,3}", t) and (l["bbox"][3] < 0.08 * H or l["bbox"][1] > 0.9 * H):
                out.append(t)
    return out


def cell_tokens(page, tables):
    """Number tokens read cell by cell (Docling cell boxes + PyMuPDF find_tables cells), so a sign or range that a
    cell wraps over two lines stays one token ('PaO2/FiO2 ≤' / '300' -> '≤300')."""
    from build_unified import decoded_words, words_in
    words = decoded_words(page)
    texts = []
    for t in tables:
        for c in t["data"]["table_cells"]:
            b = c.get("bbox") or {}
            if b.get("coord_origin") == "TOPLEFT":
                texts.append(words_in(words, (b["l"], b["t"], b["r"], b["b"])))
    try:
        for ft in page.find_tables().tables:
            for r in ft.rows:
                for c in r.cells:
                    if c:
                        texts.append(words_in(words, tuple(c)))
    except Exception:
        pass
    return [tok for x in texts for tok in numbers(x)]


def coverage(doc, by_page, dl, pages_subset=None, ref_minus=None):
    """Checks 1-2 + symbols for every page (or pages_subset). by_page: {page: [{"content", "type", ...}]}.
    ref_minus: {page: text} whose numbers/symbols are removed from the reference first (text deliberately left
    out of the output, e.g. reference lists that stage 4 excludes from the index).
    -> pages (per-page records), tot (Counter), image_only, flagged_words, flagged_nums"""
    from build_unified import ref_text
    pics_per_page = collections.Counter(p["prov"][0]["page_no"] for p in dl["pictures"])
    dl_tables = collections.defaultdict(list)
    for t in dl["tables"]:
        if t.get("prov"):
            dl_tables[t["prov"][0]["page_no"]].append(t)
    pages, flagged_words, flagged_nums, image_only = {}, [], [], []
    tot = collections.Counter()
    for i in range(doc.page_count):
        pno = i + 1
        if pages_subset is not None and pno not in pages_subset:
            continue
        ref = ref_text(doc[i])                       # text layer with Symbol/Wingdings glyphs decoded
        out = "\n".join(b["content"] for b in by_page.get(pno, []))
        # Check 1
        rw = sorted(set(words(norm_text(ref))))
        ow = set(words(norm_text(out)))
        missing_w = [w for w in rw if w not in ow]
        wcov = 1 - len(missing_w) / len(rw) if rw else None
        # Check 2
        rn = numbers(ref)
        for pn in margin_numbers(doc[i]):                       # running page numbers (top/bottom margin)
            if pn in rn:
                rn.remove(pn)
        if ref_minus and ref_minus.get(pno):
            for t in numbers(ref_minus[pno]):
                if t in rn:
                    rn.remove(t)
        on = collections.Counter(numbers(out))
        on_bare = collections.Counter(x for t in numbers(out) for x in bare(t))
        exact, value, missing, changed = 0, 0, [], []
        for t in rn:
            if on[t] > 0:
                on[t] -= 1
                exact += 1
                value += 1
                for x in bare(t):
                    on_bare[x] -= 1
            elif all(on_bare[x] > 0 for x in bare(t)):
                for x in bare(t):
                    on_bare[x] -= 1
                value += 1
                changed.append(t)                                # values there, comparator/range form differs
            else:
                missing.append(t)
        # second pass for tokens that are not an exact match: read the PDF table cells instead of lines
        resolved = []
        if changed or missing:
            out_tokens = set(numbers(out))
            ct = [x for x in cell_tokens(doc[i], dl_tables.get(pno, [])) if x in out_tokens]
            for t in list(changed):
                if any(set(bare(t)) <= set(bare(x)) for x in ct):
                    changed.remove(t); resolved.append(t); exact += 1
        # special symbols (decoded Symbol-font glyphs and their Unicode equivalents)
        rs = collections.Counter(c for c in norm_text(ref) if c in SYMBOLS)
        if ref_minus and ref_minus.get(pno):
            rs -= collections.Counter(c for c in norm_text(ref_minus[pno]) if c in SYMBOLS)
        os_ = collections.Counter(c for c in norm_text(out) if c in SYMBOLS)
        sym_missing = {c: n - os_[c] for c, n in rs.items() if os_[c] < n}
        kinds = collections.Counter(b["type"] for b in by_page.get(pno, []))
        # image-only: (almost) no text layer but the page has pictures -> content is only in images
        is_image_only = len(ref.strip()) < 200 and pics_per_page.get(pno, 0) > 0
        rec = {"page": pno, "ref_chars": len(ref.strip()), "pictures": pics_per_page.get(pno, 0),
               "block_types": dict(kinds), "image_only": is_image_only,
               "words_ref": len(rw), "words_found": len(rw) - len(missing_w),
               "word_coverage": round(wcov, 4) if wcov is not None else None, "missing_words": missing_w,
               "numbers_ref": len(rn), "numbers_exact": exact, "numbers_value": value,
               "numbers_missing": missing, "numbers_form_changed": changed, "all_ref_numbers": rn,
               "numbers_exact_by_cell_reading": resolved,
               "symbols_ref": sum(rs.values()), "symbols_missing": sym_missing}
        pages[pno] = rec
        if is_image_only:
            image_only.append(pno)
            continue
        tot["pages_checked"] += 1
        tot["words_ref"] += len(rw); tot["words_found"] += len(rw) - len(missing_w)
        tot["nums_ref"] += len(rn); tot["nums_exact"] += exact; tot["nums_value"] += value
        tot["sym_ref"] += sum(rs.values()); tot["sym_missing"] += sum(sym_missing.values())
        if wcov is not None and wcov < WORD_FLAG:
            flagged_words.append(pno)
        if missing:
            flagged_nums.append(pno)
    return pages, tot, image_only, flagged_words, flagged_nums


def main(unified=UNIFIED, report=REPORT, review_path=REVIEW):
    import pymupdf
    global ref_text
    from build_unified import ref_text
    doc = pymupdf.open(PDF)
    blocks = [json.loads(l) for l in open(unified)]
    by_page = collections.defaultdict(list)
    for b in blocks:
        by_page[b["page"]].append(b)
    dl = json.load(open(DOCLING))
    pages, tot, image_only, flagged_words, flagged_nums = coverage(doc, by_page, dl)

    # Check 3: figures
    desc = collections.Counter(json.loads(l)["picture_ref"] for l in open(DESC))
    skip = {}
    for l in open(SKIP):
        r = json.loads(l)
        skip.setdefault(r["picture_ref"], []).append("skipped-small" if r.get("reason") == "small" else "DECORATIVE")
    in_unified = collections.Counter(b["metadata"].get("picture_ref") for b in blocks if b["type"] == "image")
    fig = {"described": 0, "DECORATIVE": 0, "skipped-small": 0}
    problems = []
    for p in dl["pictures"]:
        ref = p["self_ref"]
        states = ["described"] * desc[ref] + skip.get(ref, [])
        if len(states) != 1:
            problems.append({"picture_ref": ref, "page": p["prov"][0]["page_no"], "states": states})
            continue
        fig[states[0]] += 1
        if states[0] == "described" and in_unified[ref] != 1:
            problems.append({"picture_ref": ref, "page": p["prov"][0]["page_no"],
                             "states": states, "in_unified_output": in_unified[ref]})

    # Check 4: leftovers
    left = {"attachment_markers": sum(b["content"].count("<attachment>") for b in blocks),
            "empty_blocks": [b["id"] for b in blocks if not b["content"].strip()],
            "blocks_under_5_chars": [(b["id"], b["content"]) for b in blocks if 0 < len(b["content"].strip()) < 5],
            "repeated_word_loops": [(b["id"], b["page"], b["type"], loop_score(b["content"]))
                                    for b in blocks if loop_score(b["content"]) >= 6]}

    summary = {
        "pages_total": doc.page_count,
        "pages_checked": tot["pages_checked"],
        "pages_image_only_not_checked": image_only,
        "word_coverage": round(tot["words_found"] / tot["words_ref"], 4),
        "number_coverage_exact": round(tot["nums_exact"] / tot["nums_ref"], 4),
        "number_coverage_value": round(tot["nums_value"] / tot["nums_ref"], 4),
        "numbers_ref": tot["nums_ref"], "numbers_missing": tot["nums_ref"] - tot["nums_value"],
        "symbols_ref": tot["sym_ref"], "symbols_missing": tot["sym_missing"],
        "pages_with_missing_symbols": [p for p, r in pages.items() if r.get("symbols_missing") and not r["image_only"]],
        "pages_flagged_words_below_90": flagged_words,
        "pages_flagged_missing_numbers": flagged_nums,
        "figures": fig, "figures_unaccounted": problems,
        "leftovers": {k: (len(v) if isinstance(v, list) else v) for k, v in left.items()},
    }
    json.dump({"summary": summary, "leftovers": left, "pages": pages}, open(report, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False)[:3000])

    review(doc, pages, by_page, review_path)
    return summary


# ---------------------------------------------------------------- Check 5
def pick_pages(pages, by_page):
    def kind(p):
        t = pages[p]["block_types"]
        if t.get("algorithm") or any(b["type"] == "image" and b["metadata"].get("image_type") == "flowchart"
                                     for b in by_page.get(p, [])):
            return "flowchart"
        if t.get("table"):
            return "table"
        return "text" if t.get("text") and pages[p]["words_ref"] > 50 else None
    want = {"text": 8, "table": 6, "flowchart": 6}
    chosen = {p: kind(p) or "text" for p in FORCED}
    have = collections.Counter(chosen.values())
    rng = random.Random(0)
    for k, n in want.items():
        pool = [p for p in pages if kind(p) == k and p not in chosen and not pages[p]["image_only"]]
        # half from pages with problems (most missing numbers / lowest coverage), half random
        bad = sorted(pool, key=lambda p: (-len(pages[p]["numbers_missing"]), pages[p]["word_coverage"] or 1))
        need = max(0, n - have[k])
        take = bad[:need - need // 2]
        rest = [p for p in pool if p not in take]
        take += rng.sample(rest, min(len(rest), need // 2))
        for p in take:
            chosen[p] = k
    return dict(sorted(chosen.items()))


def page_jpeg(pno):
    from PIL import Image
    img = Image.open(os.path.join(PAGES, f"page_{pno:04d}.png")).convert("RGB")
    img.thumbnail((900, 1300))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode()


def mark_missing(text, missing):
    """HTML-escape text and wrap the missing numbers (as they appear in the PDF text) in red."""
    t = html.escape(norm_text(text))
    for m in sorted(set(missing), key=len, reverse=True):
        pat = re.escape(html.escape(m)).replace(r"\-", r"\s*-\s*")
        t = re.sub(r"(?<![\d.])(" + pat + r")(?![\d.])", r'<mark class="miss">\1</mark>', t)
    return t


def review(doc, pages, by_page, review_path=REVIEW):
    chosen = pick_pages(pages, by_page)
    css = """
:root{--bg:#fff;--fg:#1d1d1f;--muted:#666;--card:#f6f6f7;--line:#ddd;--red:#c62828;--redbg:#fde7e7;--chip:#e8eef9}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161618;--fg:#e9e9ea;--muted:#9a9a9f;--card:#202023;--line:#333;--red:#ff6b6b;--redbg:#4a1f1f;--chip:#24324a}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:20px;margin:0 0 4px} .muted{color:var(--muted)}
nav{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 20px} nav a{background:var(--chip);color:var(--fg);padding:3px 8px;border-radius:6px;text-decoration:none;font-size:13px}
section{border-top:1px solid var(--line);padding:16px 0}
.row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
@media (max-width:900px){.row{grid-template-columns:1fr}}
img{width:100%;height:auto;border:1px solid var(--line);border-radius:4px}
.blk{background:var(--card);border-radius:6px;padding:8px 10px;margin:0 0 8px;white-space:pre-wrap;word-break:break-word;font-size:13px}
.tag{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);display:block;margin-bottom:4px}
.missbox{background:var(--redbg);color:var(--red);border-radius:6px;padding:8px 10px;margin:0 0 10px;font-weight:600}
mark.miss{background:var(--redbg);color:var(--red);font-weight:700;padding:0 2px;border-radius:3px}
details{margin-top:8px} summary{cursor:pointer;color:var(--muted)}
.ref{white-space:pre-wrap;font-size:12px;background:var(--card);padding:8px;border-radius:6px;max-height:420px;overflow:auto}
.stats{font-size:13px;margin:4px 0 10px}"""
    parts = [f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
             f"<title>Extraction Review Sheet</title><style>{css}</style></head><body>",
             "<h1>Extraction review sheet</h1><div class=muted>Left: the PDF page. Right: blocks in out/unified_output.jsonl for "
             "that page. Numbers in the PDF text layer that are missing from the blocks are listed in red, and marked red "
             "in the PDF text (expand below the blocks).</div><nav>"]
    parts += [f"<a href='#p{p}'>p{p} · {k}</a>" for p, k in chosen.items()]
    parts.append("</nav>")
    for p, k in chosen.items():
        r = pages[p]
        wc = "n/a" if r["word_coverage"] is None else f"{r['word_coverage']:.0%}"
        parts.append(f"<section id=p{p}><h2>Page {p} <span class=muted>· {k}{' · image-only page' if r['image_only'] else ''}</span></h2>"
                     f"<div class=stats>words {r['words_found']}/{r['words_ref']} ({wc}) · numbers by value "
                     f"{r['numbers_value']}/{r['numbers_ref']}, exact {r['numbers_exact']}/{r['numbers_ref']}</div><div class=row>"
                     f"<div><img loading=lazy alt='page {p}' src='data:image/jpeg;base64,{page_jpeg(p)}'></div><div>")
        if r["numbers_missing"]:
            parts.append(f"<div class=missbox>Missing numbers: {html.escape(', '.join(r['numbers_missing']))}</div>")
        if r["numbers_form_changed"]:
            parts.append(f"<div class=muted>Value present but sign/range written differently: "
                         f"{html.escape(', '.join(r['numbers_form_changed']))}</div>")
        for b in by_page.get(p, []):
            parts.append(f"<div class=blk><span class=tag>{b['type']} · {b['source']} · {b['id']}</span>{html.escape(b['content'])}</div>")
        ref = ref_text(doc[p - 1])
        parts.append(f"<details><summary>PDF text layer (missing numbers in red)</summary><div class=ref>"
                     f"{mark_missing(ref, r['numbers_missing'])}</div></details></div></div></section>")
    parts.append("</body></html>")
    open(review_path, "w", encoding="utf-8").write("".join(parts))
    print(f"wrote {review_path} ({os.path.getsize(review_path) / 1e6:.1f} MB): pages {list(chosen)}")


if __name__ == "__main__":
    main()
