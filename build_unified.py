#!/usr/bin/env python
"""Build out/unified_output.jsonl with the PDF's own text layer as the primary source.

    ../miniconda3/envs/senv/bin/python build_unified.py      # CPU, login node (needs pymupdf)

The PDF is a Word 2019 export with a real text layer on 469/474 pages. Sources, in order of preference:
  text      "pdf_text"          paragraphs/headings/bullets rebuilt from PyMuPDF line/span data
            "chandra"           pages 4-8 (no text layer: scanned images)
  table     "docling+pdf_text"  every Docling table: the mmore markdown table is kept when its shape matches the
                                Docling grid, and each cell is checked against the text-layer words inside the
                                Docling cell box; differing cells take the text-layer value. Shape mismatch, or
                                FORCE_GRID pages -> table rebuilt from the Docling grid with text-layer values.
            "pdf_text_table"    tables Docling missed, found by PyMuPDF find_tables() (e.g. p256)
            "mmore"             fallback: a Docling table whose cells have no text-layer words (scanned table)
  algorithm "chandra"           unchanged: copied from the mmore-based build (out/unified_output.mmore.jsonl)
  image     "qwen3"             unchanged: out/image_descriptions.jsonl
  text      "pdf_text" + metadata.in_figure   text-layer words inside a Docling picture (diagrams drawn as Word
                                shapes), one block per picture, placed after its image block
Blocks on a page are ordered top to bottom. Superscripts are written with '^' (10^9/L, footnote 2030^1).
Outputs: out/unified_output.jsonl, out/merge_report.json
Run as stage 2 of run_pipeline.py, it writes to out/pipeline/stage2_extract/ and replaces non-English text with the
stage-1 NLLB translations (source "nllb-1.3b", original in metadata.original_text / original_language).
"""
import collections, json, os, re, unicodedata

import merge_sources as M

ROOT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(ROOT, "data", "source.pdf")
OLD = os.path.join(ROOT, "out", "unified_output.mmore.jsonl")
OUT = os.path.join(ROOT, "out", "unified_output.jsonl")
REPORT = os.path.join(ROOT, "out", "merge_report.json")
NO_TEXT_LAYER = [4, 5, 6, 7, 8]
FORCE_GRID = {287}                       # mmore table structure known to be wrong (TIMI score)
STACKED = {287}                          # tables whose rows are newline-stacked lists in one PDF row (see stacked_tables)
BULLETS = set("•▪◦●○■□➢➤►✓✔-–o") | {chr(c) for c in range(0xF000, 0xF100)}
MAX_TEXT = 1500


# ---------------------------------------------------------------- Symbol / Wingdings glyphs
# Word stores some characters in the old Symbol font encoding; in the text layer they come out as private-use
# code points (U+F0xx) that look like nothing: 'Dobutamine 3-5 \uf06dg/kg/min' is 3-5 μg/kg/min, '\uf0a3 100 mmHg'
# is ≤ 100. Decode them with the Adobe Symbol encoding; Wingdings glyphs are list bullets/checkboxes.
_SYM = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖαβχδεφγηιϕκλμνοπθρστυϖωξψζ"))
_SYM.update({"\x20": " ", "\x22": "∀", "\x24": "∃", "\x27": "∋", "\x2a": "∗", "\x2b": "+", "\x2d": "−", "\x3c": "<",
             "\x3d": "=", "\x3e": ">", "\x40": "≅", "\x5e": "⊥", "\x7e": "∼", "\x95": "•", "\xa2": "′", "\xa3": "≤",
             "\xa5": "∞", "\xab": "↔", "\xac": "←", "\xad": "↑", "\xae": "→", "\xaf": "↓", "\xb0": "°", "\xb1": "±",
             "\xb2": "″", "\xb3": "≥", "\xb4": "×", "\xb5": "∝", "\xb7": "•", "\xb8": "÷", "\xb9": "≠", "\xba": "≡",
             "\xbb": "≈", "\xbc": "…", "\xd6": "√", "\xd7": "⋅", "\xdb": "⇔", "\xde": "⇒", "\xdf": "⇓"})
_WD3 = {"\x8b": "↑", "\x8c": "↓", "\x86": "←", "\x87": "→"}


def decode(text, font):
    """Map private-use glyphs of Symbol/Wingdings fonts to real characters."""
    if not any(0xF000 <= ord(c) <= 0xF0FF for c in text):
        return text
    out = []
    for c in text:
        o = ord(c)
        if not 0xF000 <= o <= 0xF0FF:
            out.append(c)
            continue
        k = chr(o - 0xF000)
        if "Symbol" in font:
            out.append(_SYM.get(k, "•"))
        elif "Wingdings3" in font:
            out.append(_WD3.get(k, "•"))
        else:                                                # Wingdings / Wingdings2: bullets, checkboxes
            out.append(" " if k == " " else "•")
    return "".join(out)


def ref_text(page):
    """Whole-page text with glyphs decoded (used as the reference by verify_output.py)."""
    rows = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            rows.append((l["bbox"][1], l["bbox"][0], "".join(decode(s["text"], s["font"]) for s in l["spans"])))
    rows.sort(key=lambda r: (round(r[0] / 3), r[1]))
    return "\n".join(r[2] for r in rows)


# ---------------------------------------------------------------- text layer -> lines
def line_text(line):
    """Span texts joined; raised smaller spans written as ^x (10^9, footnote markers)."""
    spans = [s for s in line["spans"] if s["text"]]
    if not spans:
        return ""
    big = max(s["size"] for s in spans)
    base = max(s["origin"][1] for s in spans if s["size"] >= big - 0.5)
    out = ""
    for s in spans:
        t = decode(s["text"], s["font"])
        raised = (s["flags"] & 1) or (s["size"] < 0.85 * big and s["origin"][1] < base - 1.5)
        if raised and t.strip():
            out = out.rstrip() + "^" + t.strip() + (" " if t.endswith(" ") else "")
        else:
            out += t
    return unicodedata.normalize("NFC", out)


def is_bold(line):
    sp = [s for s in line["spans"] if s["text"].strip()]
    return bool(sp) and all((s["flags"] & 16) or "Bold" in s["font"] for s in sp)


def page_lines(page):
    """[(y0, x0, text, bold, size, bbox)] for every non-empty line, page number lines removed."""
    H = page.rect.height
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = line_text(l).strip()
            if not t:
                continue
            y0, y1 = l["bbox"][1], l["bbox"][3]
            if re.fullmatch(r"\d{1,3}", t) and (y1 < 0.08 * H or y0 > 0.9 * H):
                continue                                   # running page number
            size = max(s["size"] for s in l["spans"] if s["text"].strip())
            out.append((round(y0, 1), round(l["bbox"][0], 1), t, is_bold(l), size, l["bbox"], b["number"]))
    return out


def to_markdown(lines):
    """Lines (same order as the PDF blocks) -> markdown paragraphs [(y, text)]."""
    paras, cur, cur_y, cur_blk = [], [], None, None
    right = collections.defaultdict(float)                 # right edge of each PDF block
    for ln in lines:
        right[ln[6]] = max(right[ln[6]], ln[5][2])
    pending, prev_x1 = None, None

    def flush():
        if cur:
            paras.append((cur_y, " ".join(cur).replace("  ", " ")))

    for y, x, t, bold, size, bbox, blk in lines:
        first = t[:1]
        bullet = first in BULLETS and (len(t) == 1 or t[1] == " ")
        if bullet and not t[1:].strip():                     # bullet glyph alone on its line: applies to the next line
            pending = "  - " if first in "o◦○" else "- "
            prev_x1 = None
            continue
        if pending:
            t, bullet, first = pending + t, True, "-"
            pending = None
        elif blk == cur_blk and cur and prev_x1 is not None and prev_x1 < right[blk] - 90:
            flush(); cur = []                                # previous line ended early: Word line break
        prev_x1 = bbox[2]
        heading = (bold or size >= 13) and len(t) < 120 and not bullet and not t.endswith((".", ",", ";"))
        if bullet and not t.startswith(("- ", "  - ")):
            body = t[1:].strip()
            t = ("  - " if first in "o◦○" else "- ") + body if body else ""
        if heading:
            flush(); cur, cur_y = [], None
            paras.append((y, "## " + t.strip("* ")))
            cur_blk = blk
            continue
        if bullet or blk != cur_blk or not cur:
            flush()
            cur, cur_y = [t] if t else [], y
        else:
            if cur and cur[-1] in ("- ", "  - ") or (cur and re.fullmatch(r"\s*-\s*", cur[-1] or "")):
                cur[-1] = cur[-1] + t
            else:
                cur.append(t)
        cur_blk = blk
    flush()
    # a bullet glyph alone on its line followed by its text on the next line -> merge
    merged = []
    for y, t in paras:
        if merged and re.fullmatch(r"\s*-\s*", merged[-1][1]):
            merged[-1] = (merged[-1][0], merged[-1][1].rstrip() + " " + t)
        else:
            merged.append((y, t))
    merged = [(y, t) for y, t in merged if t.strip() and not re.fullmatch(r"\s*-\s*", t)]
    # 'V.' / 'XI.' / 'A' are separate text runs in the Word file: attach them to the following paragraph/heading
    out = []
    for y, t in merged:
        core = t[3:] if t.startswith("## ") else t
        if out and out[-1][2]:
            py, pt, _ = out.pop()
            hd = t.startswith("## ") or pt.startswith("## ")
            t = ("## " if hd else "") + pt.replace("## ", "", 1) + " " + core
            y, core = py, t[3:] if t.startswith("## ") else t
        prefix = bool(re.fullmatch(r"(?:[IVXLC]+|[A-Z]|\d{1,2})[.)]?", core.strip()))
        out.append((y, t, prefix))
    return [(y, t) for y, t, _ in out]


def pack(paras):
    """Markdown paragraphs -> text blocks [(y, content)] split at headings / MAX_TEXT chars."""
    out, cur, cy = [], "", None
    for y, p in paras:
        if (p.startswith("#") and cur and not cur.lstrip().startswith("#")) or len(cur) + len(p) > MAX_TEXT:
            if cur:
                out.append((cy, cur))
            cur, cy = p, y
        else:
            cur, cy = (f"{cur}\n{p}" if cur else p), (cy if cur else y)
    if cur:
        out.append((cy, cur))
    return out


# ---------------------------------------------------------------- tables
def decoded_words(page):
    """page.get_text('words') with Symbol/Wingdings glyphs decoded (font looked up from the span under the word)."""
    words = page.get_text("words")
    if not any(any(0xF000 <= ord(c) <= 0xF0FF for c in w[4]) for w in words):
        return words
    spans = [(pymupdf_rect(s["bbox"]), s["font"]) for b in page.get_text("dict")["blocks"]
             for l in b.get("lines", []) for s in l["spans"] if any(0xF000 <= ord(c) <= 0xF0FF for c in s["text"])]
    out = []
    for w in words:
        if any(0xF000 <= ord(c) <= 0xF0FF for c in w[4]):
            cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            font = next((f for r, f in spans if r[0] - 1 <= cx <= r[2] + 1 and r[1] - 1 <= cy <= r[3] + 1), "Symbol")
            w = (*w[:4], decode(w[4], font), *w[5:])
        out.append(w)
    return out


def pymupdf_rect(b):
    return tuple(b)


def words_in(words, bb):
    """Text-layer words whose centre lies in bb=(x0,y0,x1,y1), in reading order."""
    w = [x for x in words if bb[0] <= (x[0] + x[2]) / 2 <= bb[2] and bb[1] <= (x[1] + x[3]) / 2 <= bb[3]]
    w.sort(key=lambda x: (x[5], x[6], x[7]))                 # block, line, word number
    return " ".join(x[4] for x in w)


def norm_cell(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"<br\s*/?>|</?(?:sup|sub|b|i)>|\*\*", " ", s)
    s = re.sub(r"[‐-―−]", "-", s)
    return re.sub(r"\s+", "", s).lower()


def md_table_cells(md):
    rows = [r for r in md.strip().splitlines() if r.strip().startswith("|")]
    rows = [r for r in rows if not re.fullmatch(r"\s*\|[\s|:-]*\|\s*", r)]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]


def render(grid):
    lines = ["| " + " | ".join(c.replace("|", "/") for c in r) + " |" for r in grid]
    if lines:
        lines.insert(1, "|" + "---|" * len(grid[0]))
    return "\n".join(lines)


def orphan_words(t, words, table_box):
    """Words inside the table area that no Docling cell box covers (e.g. list numbers '1.' of a reference list that
    Docling read as a table) -> {(row, col): [(x, word), ...]} of the nearest cell on the same row."""
    cells = [(c["start_row_offset_idx"], c["start_col_offset_idx"], c["bbox"]) for c in t["data"]["table_cells"]
             if (c.get("bbox") or {}).get("coord_origin") == "TOPLEFT"]
    out = collections.defaultdict(list)
    for w in words:
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        if not (table_box[0] - 2 <= cx <= table_box[2] + 2 and table_box[1] - 2 <= cy <= table_box[3] + 2):
            continue
        if any(b["l"] <= cx <= b["r"] and b["t"] <= cy <= b["b"] for _, _, b in cells):
            continue
        row = [(r, c, b) for r, c, b in cells if b["t"] - 2 <= cy <= b["b"] + 2]
        if row:
            r, c, b = min(row, key=lambda x: min(abs(cx - x[2]["l"]), abs(cx - x[2]["r"])))
            out[(r, c)].append((w[0] < b["l"], w[4]))
    return out


def docling_table(t, words, mm_md, force_grid, table_box=None):
    """-> (content, source, metadata) for one Docling table."""
    d = t["data"]
    R, C = d["num_rows"], d["num_cols"]
    grid = [["" for _ in range(C)] for _ in range(R)]
    layer = [["" for _ in range(C)] for _ in range(R)]
    for c in d["table_cells"]:
        r0, c0 = c["start_row_offset_idx"], c["start_col_offset_idx"]
        b = c.get("bbox") or {}
        grid[r0][c0] = c["text"]
        layer[r0][c0] = words_in(words, (b["l"], b["t"], b["r"], b["b"])) if b.get("coord_origin") == "TOPLEFT" else ""
    if table_box:
        for (r, c), ws in orphan_words(t, words, table_box).items():
            before = " ".join(w for left, w in ws if left)
            after = " ".join(w for left, w in ws if not left)
            layer[r][c] = " ".join(x for x in (before, layer[r][c], after) if x)
    has_layer = any(any(x for x in r) for r in layer)
    meta = {"docling_grid": M.grid_meta(t)}
    if not has_layer:                                        # scanned table: nothing to check against
        return (mm_md or M.grid_markdown(t)), ("mmore" if mm_md else "docling"), meta
    mm = md_table_cells(mm_md) if mm_md else None
    corrected = []
    if mm and not force_grid and len(mm) == R and all(len(r) == C for r in mm):
        out = [row[:] for row in mm]
        for i in range(R):
            for j in range(C):
                if layer[i][j] and norm_cell(mm[i][j]) != norm_cell(layer[i][j]):
                    corrected.append({"row": i, "col": j, "was": mm[i][j], "now": layer[i][j]})
                    out[i][j] = layer[i][j]
        meta["cells_corrected_from_pdf_text"] = corrected
        return render(out), "mmore_table+pdf_text", meta
    out = [[layer[i][j] or grid[i][j] for j in range(C)] for i in range(R)]
    meta["rebuilt_from"] = "docling_grid+pdf_text" + (" (forced)" if force_grid else " (mmore shape differs)")
    return render(out), "docling_grid+pdf_text", meta


def stacked_tables(page, words):
    """The TIMI STEMI score (p287) is two side-by-side lists in one ruled row: risk indicators with their points,
    and total score -> 30-day mortality %, odds of death. Docling's grid and mmore both mis-align it.
    PyMuPDF's find_tables() keeps each column as a newline-separated list, which preserves the order, so the two
    real tables are rebuilt from those lists (all values from the text layer)."""
    out = []
    for ft in page.find_tables().tables:
        rows = ft.extract()
        big = [r for r in rows if r and any(c and c.count("\n") >= 5 for c in r)]
        if not big:
            continue
        r = [(c or "") for c in big[0]]
        labels = [x.strip() for x in r[0].split("\n") if x.strip()]
        points = [x.strip() for x in r[1].split("\n") if x.strip()]
        items = [l for l in labels if l.startswith("-") or l.lower().startswith("total possible")]
        if len(items) != len(points):
            return None                                       # cannot pair safely -> caller keeps the grid version
        a, k = [["Risk indicator", "Points"]], 0
        for l in labels:
            if l.startswith("-") or l.lower().startswith("total possible"):
                a.append([l.lstrip("- ").strip() if l.startswith("-") else l, points[k]]); k += 1
            else:
                a.append([f"**{l}**", ""])
        cols = [[x.strip() for x in (c or "").split("\n") if x.strip()] for c in r[2:]]
        n = len(cols[0])
        if any(len(c) != n for c in cols):
            return None
        b = [["Total score", "30-day mortality %", "Odds of death"]] + [[cols[0][i], cols[1][i], cols[2][i]] for i in range(n)]
        out.append((ft.bbox, a, b))
    return out


# ---------------------------------------------------------------- main
def main(out=OUT, report_path=REPORT, translations=None):
    """translations: stage-1 translations.jsonl; Khmer/Lao/Vietnamese text in the blocks is replaced by it."""
    import pymupdf
    pdf = pymupdf.open(PDF)
    dl = json.load(open(M.DOCLING))
    sizes = {int(k): v["size"] for k, v in dl["pages"].items()}

    def topleft(b, page):
        H = sizes[page]["height"]
        return (b["l"], H - b["t"], b["r"], H - b["b"]) if b.get("coord_origin", "BOTTOMLEFT") == "BOTTOMLEFT" \
            else (b["l"], b["t"], b["r"], b["b"])

    tables = collections.defaultdict(list)
    for t in dl["tables"]:
        if t.get("prov") and t["label"] == "table":
            tables[t["prov"][0]["page_no"]].append(t)
    pictures = collections.defaultdict(list)
    for p in dl["pictures"]:
        pictures[p["prov"][0]["page_no"]].append(p)
    old = [json.loads(l) for l in open(OLD)]
    algos = collections.defaultdict(list)
    for b in old:
        if b["type"] == "algorithm":
            algos[b["page"]].append(b)
    descs = {}
    for l in open(M.IMAGES):
        r = json.loads(l)
        descs[r["picture_ref"]] = r
    chandra = {json.loads(l)["page"]: json.loads(l)["content"] for l in open(M.CHANDRA)}
    # mmore markdown tables per page (to keep their structure where it matches Docling)
    mm = json.load(open(M.MMORE))
    starts = {}
    for off, pg, _ in mm["metadata"]["paragraph_starts"]:
        if pg >= 1:
            starts.setdefault(pg, off)
    pgs = sorted(starts)
    mm_tables = {}
    for i, p in enumerate(pgs):
        txt = mm["text"][starts[p]:(starts[pgs[i + 1]] if i + 1 < len(pgs) else len(mm["text"]))]
        mm_tables[p] = [m.group(0) for m in re.finditer(r"(?:^\|.*\|[ \t]*(?:\n|$))+", txt, re.M)]

    sec_starts = M.section_starts(dl)
    blocks, stats = [], collections.Counter()
    for pno in range(1, pdf.page_count + 1):
        page = pdf[pno - 1]
        (chap, sec, num), starting = M.locate(sec_starts, pno)
        items = []                                           # (y, order, block)

        def add(y, btype, source, content, **meta):
            if content and content.strip():
                items.append((y, len(items), {"page": pno, "type": btype, "source": source, "content": content.strip(),
                                              "metadata": {k: v for k, v in meta.items() if v is not None}}))

        words = decoded_words(page)
        # --- tables: Docling first, then PyMuPDF find_tables for tables Docling missed
        cell_boxes = []
        page_mm = list(mm_tables.get(pno, []))
        stacked = stacked_tables(page, words) if pno in STACKED else None
        for t in tables.get(pno, []):
            mm_md = page_mm.pop(0) if page_mm else None
            tb = topleft(t["prov"][0]["bbox"], pno)
            st = next((x for x in stacked or [] if pymupdf.Rect(x[0]).intersects(pymupdf.Rect(tb))), None)
            if st:
                add(tb[1], "table", "pdf_text_table", render(st[1]), docling_grid=M.grid_meta(t),
                    rebuilt_from="pdf_text find_tables (two stacked lists: risk indicator -> points)")
                add(tb[1] + 0.1, "table", "pdf_text_table", render(st[2]), docling_grid=M.grid_meta(t),
                    rebuilt_from="pdf_text find_tables (two stacked lists: total score -> mortality)")
                stats["table_stacked_rebuilt"] += 1
                for c in t["data"]["table_cells"]:
                    b = c.get("bbox") or {}
                    if b.get("coord_origin") == "TOPLEFT":
                        cell_boxes.append((b["l"], b["t"], b["r"], b["b"]))
                cell_boxes.append(tuple(st[0]))
                continue
            content, src, meta = docling_table(t, words, mm_md, pno in FORCE_GRID, tb)
            add(tb[1], "table", src, content, **meta)
            stats[f"table_{src}"] += 1
            stats["table_cells_corrected"] += len(meta.get("cells_corrected_from_pdf_text", []))
            for c in t["data"]["table_cells"]:
                b = c.get("bbox") or {}
                if b.get("coord_origin") == "TOPLEFT":
                    cell_boxes.append((b["l"], b["t"], b["r"], b["b"]))
        if pno not in NO_TEXT_LAYER:
            try:
                found = page.find_tables().tables
            except Exception:
                found = []
            dl_boxes = [topleft(t["prov"][0]["bbox"], pno) for t in tables.get(pno, [])]
            for ft in found:
                bb = ft.bbox
                if any(pymupdf.Rect(bb).intersects(pymupdf.Rect(d)) for d in dl_boxes):
                    continue
                rows = ft.extract()
                if len(rows) < 2 or max(len(r) for r in rows) < 2:
                    continue
                grid = [[re.sub(r"\s+", " ", c or "").strip() for c in r] for r in rows]
                filled_cols = sum(any(r[j] for r in grid if j < len(r)) for j in range(max(len(r) for r in grid)))
                if filled_cols < 2 or sum(1 for r in grid if sum(bool(c) for c in r) >= 2) < 2:
                    stats["find_tables_rejected"] += 1           # a box around text, not a table
                    continue
                add(bb[1], "table", "pdf_text_table", render(grid),
                    pdf_table={"bbox": list(bb), "num_rows": len(grid), "num_cols": len(grid[0])})
                stats["table_pdf_text_table"] += 1
                for r in ft.rows:
                    for c in r.cells:
                        if c:
                            cell_boxes.append(tuple(c))
        # --- pictures: Qwen3 description, then text-layer words drawn inside the picture
        pic_boxes = []
        for p in pictures.get(pno, []):
            pb = topleft(p["prov"][0]["bbox"], pno)
            pic_boxes.append((pb, p["self_ref"]))
            r = descs.get(p["self_ref"])
            if r:
                add(pb[1], "image", "qwen3", r["description"], bbox=r["bbox"], image_path=r["image_path"],
                    image_type=r["type"], picture_ref=r["picture_ref"])
        if algos.get(pno):
            y = min((b[0][1] for b in pic_boxes), default=0)
            for a in algos[pno]:
                add(y - 0.1, "algorithm", "chandra", a["content"])
        # --- text
        if pno in NO_TEXT_LAYER:
            for y, c in pack([(i, p) for i, p in enumerate(M.split_text(M.html_to_text(chandra.get(pno, ""))))]):
                add(y, "text", "chandra", c)
            stats["pages_chandra_text"] += 1
        else:
            body, fig = [], collections.defaultdict(list)
            for ln in page_lines(page):
                cx, cy = (ln[5][0] + ln[5][2]) / 2, (ln[5][1] + ln[5][3]) / 2
                if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in cell_boxes):
                    continue                                 # inside a table cell -> in the table block
                pic = next((ref for b, ref in pic_boxes if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]), None)
                (fig[pic] if pic else body).append(ln)
            for y, c in pack(to_markdown(body)):
                add(y, "text", "pdf_text", c)
            for ref, lns in fig.items():
                if len("".join(l[2] for l in lns)) < 5 and not re.search(r"\d", "".join(l[2] for l in lns)):
                    continue                                 # lone diagram labels ('A', 'F')
                lns.sort(key=lambda l: (round(l[0] / 4), l[1]))
                add(lns[0][0] + 0.05, "text", "pdf_text", "\n".join(l[2] for l in lns), in_figure=ref)
                stats["figure_text_blocks"] += 1
        if not items and pno in chandra and len(re.sub(r"\s|\d", "", page.get_text())) < 5:
            # scanned page that no picture covers (e.g. p165): Chandra, as for pages 4-8
            for y, c in pack([(i, p) for i, p in enumerate(M.split_text(M.html_to_text(chandra[pno])))]):
                add(y, "text", "chandra", c)
            stats["pages_chandra_text"] += 1
        if not items:                                        # nothing from any primary source: mmore fallback
            for b in old:
                if b["page"] == pno and b["type"] == "text":
                    add(0, "text", "mmore", b["content"])
                    stats["pages_mmore_fallback"] += 1

        # --- order and section assignment
        items.sort(key=lambda x: (x[0], x[1]))
        split_y = None
        if starting:
            c, n, t = starting[-1]
            key = (t if n is not None else f"CHAPTER {c.split(' - ')[0]}").split(",")[0].split("(")[0][:20].lower()
            key = re.sub(r"\s+", " ", key).strip()
            for ln in page_lines(page) if pno not in NO_TEXT_LAYER else []:
                if key and key in re.sub(r"\s+", " ", ln[2].lower()):
                    split_y = ln[0]
                    break
            if split_y is None:
                split_y = 0
            new_sec = (c, t if n is not None else f"Chapter {c.split(' - ')[0]} introduction", n)
        for y, _, b in items:
            s = new_sec if split_y is not None and y >= split_y - 0.5 else (chap, sec, num)
            b["chapter"], b["section"], b["section_number"] = s
            blocks.append(b)

    if translations:
        from pipeline.extract import apply_translations
        stats.update(apply_translations(blocks, translations))
    order = ["id", "page", "type", "source", "chapter", "section", "section_number", "content", "metadata"]
    with open(out, "w", encoding="utf-8") as f:
        for i, b in enumerate(blocks):
            b["id"] = f"chunk_{i:05d}"
            f.write(json.dumps({k: b[k] for k in order}, ensure_ascii=False) + "\n")

    per_sec = collections.Counter(f"{b['section_number'] or '-'} {b['section']}" for b in blocks)
    covered = sorted({b["section_number"] for b in blocks if b["section_number"]})
    report = {"total_blocks": len(blocks),
              "blocks_per_type": dict(collections.Counter(b["type"] for b in blocks)),
              "blocks_per_source": dict(collections.Counter(b["source"] for b in blocks)),
              "blocks_per_section": dict(per_sec),
              "pages_total": pdf.page_count,
              "pages_with_no_content": sorted(set(range(1, pdf.page_count + 1)) - {b["page"] for b in blocks}),
              "sections_covered": f"{len(covered)}/{len(M.TOC)}",
              "images_described": sum(1 for b in blocks if b["type"] == "image"),
              "notes": dict(stats)}
    json.dump(report, open(report_path, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: report[k] for k in ["total_blocks", "blocks_per_type", "blocks_per_source", "sections_covered",
                                             "pages_with_no_content", "notes"]}, indent=1))


if __name__ == "__main__":
    main()
