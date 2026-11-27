"""Stage 4: chunk the verified unified output for retrieval (schema: chunks.jsonl of the team plan).

Sections come from the PDF's own table of contents (config.chunk.toc_pages), not from Docling headings. Each
section starts where its title line is found in the text layer (TOC page + offset, searched on nearby pages).

Rules, in priority order
  1 never cross a section boundary          (chunks are built per section region)
  2 never split a sentence                  (text is cut into sentence units first; a sentence that continues
                                             on the next page/block is joined; only a single sentence longer than
                                             the variant's max is cut, at '; ' / ', ', and flagged forced_split)
  3 tables whole; a table longer than max is split by rows with the header row repeated
  4 flowcharts whole; a Qwen3 image block and a Chandra algorithm block of the same figure -> one flowchart chunk
    with the Chandra text, Qwen3 text in metadata.alt_description
  5 other figure chunks (Qwen3 descriptions) numbers_verified = false
  6 text chunks overlap by ~15 % (whole sentences, only between consecutive text chunks of one text run)
  7 front matter (pages 1-16), chapter title pages and reference lists -> excluded.jsonl
  8 a chunk under min_tokens_flag is merged into the next chunk of the same section (metadata.merged_from);
    one at the end of a section stays as it is
Clean-up before chunking (fix_text, shared with stage 5): page-checked manual fixes from config chunk.text_fixes, then
LaTeX left in OCR'd tables -> plain text ('$4\\!-\\!6$' -> '4-6', '$0.34 \\text{m}^3$' -> '0.34 m³').
While chunking: a '#' line that continues the previous unfinished line is text, not a heading (stray_hash); a table
whose header row is only repeated score numbers (NEWS-2) gets 'Score 3 (low)' ... 'Score 3 (high)' headers
(metadata.original_header keeps the old one).
Citations use the printed page number (PDF page - page_offset, checked against each page's footer); `pages` keeps the
PDF page. Document errata (config chunk.errata) are tagged on chunks as metadata.errata; the text is not changed.
Outputs (stage4_chunk/): chunks_<variant>.jsonl, excluded.jsonl, sections.json, chunk_stats.json, text_fixes.json,
stray_headings.json; and out/pipeline/errata.json, out/pipeline/manual_review_tables.csv
"""
import collections, csv, difflib, json, os, re, statistics, time

from pipeline.common import StageFailed, inp, p, read_jsonl, stage_dir, write_json, write_jsonl

TYPE_MAP = {"text": "body_text", "table": "table", "image": "figure", "algorithm": "flowchart"}
LAYER_SOURCES = {"pdf_text", "mmore_table+pdf_text", "docling_grid+pdf_text", "pdf_text_table"}
ROMAN_HEAD = re.compile(r"^#{1,4}\s*([IVXL][IVXLl]{0,5})\s*[.\-–)]\s*(\S.*)$")


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


# ---------------------------------------------------------------- table of contents
def parse_toc(pdf, toc_pages):
    """-> chapters [(roman, title, printed_page)], sections [(num, title_raw, printed_page)], skipped lines"""
    lines = [l.strip() for pg in toc_pages for l in pdf[pg - 1].get_text().splitlines() if l.strip()]
    chapters, sections, skipped, buf = [], [], [], ""
    leader = re.compile(r"\s*\.{3,}\s*(?:Page\s*)?(\d+)\s*$", re.I)
    for l in lines:
        cur = f"{buf} {l}".strip() if buf else l
        m_ch = re.match(r"CHAPTER\s+([IVX]+)\s+(.+?)" + leader.pattern, cur, re.I)
        m = re.match(r"(\d+)\.\s+(.+?)" + leader.pattern, cur)
        if m_ch:
            chapters.append((m_ch[1], m_ch[2].strip().title(), int(m_ch[3]))); buf = ""
        elif m:
            sections.append((int(m[1]), re.sub(r"\s+", " ", m[2]).strip(), int(m[3]))); buf = ""
        elif re.match(r"\d+\.\s", l) or buf:
            buf = cur                                        # wrapped TOC entry (15, 29)
        else:
            skipped.append(l)
    return chapters, sections, skipped


def find_heading(pdf, BU, title, page, search=(0, 1, -1, 2, 3, -2)):
    """Text-layer line on/near `page` that is the section's title line -> (page, line text, ratio) or None."""
    key = letters(title)[:30]
    best = None
    for dp in search:
        pg = page + dp
        if not 1 <= pg <= pdf.page_count:
            continue
        for ln in BU.page_lines(pdf[pg - 1]):
            lk = letters(ln[2])
            if len(lk) < 4:
                continue
            r = difflib.SequenceMatcher(None, key, lk[:len(key)]).ratio()
            if r >= 0.75 and (best is None or r > best[2] + 0.05):
                best = (pg, ln[2], r)
        if best:
            return best
    return None


def fix_title(toc_title, body_line):
    """Spelling fixes from the body heading, word by word (TOC: 'Pisoning', 'Respiratonry', 'Empiric Al')."""
    body = re.findall(r"[A-Za-z]+", body_line)
    fixes, out = [], []
    if "Empiric Al" in toc_title and "EMPIRICAL" in body_line.upper():   # TOC splits the word; body: EMPIRICAL
        toc_title = toc_title.replace("Empiric Al", "Empirical")
        fixes.append(("Empiric Al", "Empirical"))
    toks = re.findall(r"[A-Za-z]+|[^A-Za-z]+", toc_title)
    for t in toks:
        if not t.isalpha():
            out.append(t); continue
        cand = max(body, key=lambda b: difflib.SequenceMatcher(None, t.lower(), b.lower()).ratio(), default=None)
        if cand and cand.lower() != t.lower() and difflib.SequenceMatcher(None, t.lower(), cand.lower()).ratio() >= 0.8 \
                and len(t) >= 4:
            new = cand.capitalize() if t[:1].isupper() else cand.lower()
            fixes.append((t, new)); out.append(new)
        else:
            out.append(t)
    title = "".join(out)
    return re.sub(r"\s+", " ", title).strip(), fixes


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


# ---------------------------------------------------------------- sentences
ABBR = {"dr", "prof", "fig", "figs", "al", "vs", "e.g", "i.e", "eg", "ie", "approx", "no", "ref", "st", "mr", "mrs",
        "ms", "ass", "jr", "inc", "etc", "tab", "vol", "ed", "eds", "p", "pp", "resp", "max", "min", "sr", "co", "dept",
        "i.v", "i.m", "s.c", "b.i.d", "t.i.d", "q.i.d", "h.e", "u.s", "cf"}


def split_sentences(line):
    """Split one line at sentence ends; abbreviations, initials and decimals do not end a sentence."""
    out, start = [], 0
    for m in re.finditer(r"[.!?](?=[\s\"”’)]*\s+[\"“(\[]?[A-Z0-9])", line):
        i = m.start()
        if line[i] == ".":
            w = re.search(r"([A-Za-z][A-Za-z.]*)$", line[start:i])
            word = w.group(1).lower() if w else ""
            if word in ABBR or (w and len(w.group(1)) == 1 and w.group(1).isupper()):
                continue                                    # 'Dr. TES', 'et al. 2013', 'J. Smith'
            if re.search(r"\d$", line[start:i]) and re.match(r"\s*\d", line[i + 1:]):
                continue                                    # '1. 2' list numbers / '2.5'
            if re.fullmatch(r"\s*(?:[-•]\s*)?(?:\d{1,2}|[a-zA-Z]|[IVXL]+)", line[start:i]):
                continue                                    # list label '1.' 'a.' 'IV.'
        end = m.end()
        out.append(line[start:end].strip()); start = end
    if line[start:].strip():
        out.append(line[start:].strip())
    return out


CONNECTIVE = re.compile(r"(?:\b(?:of|and|or|the|to|with|in|for|a|an|by|on|at|from|as|is|are|than|that|which|"
                        r"if|when|after|before|per|without|within|including|such)|[,(/+-])$", re.I)


def continues(prev, line):
    """Does `line` continue the unfinished sentence `prev` (a Word line break or a page break mid-sentence)?"""
    if ends_sentence(prev) or re.match(r"\s*(?:[-•▪◦●+]|\d+[.)]\s|[a-z][.)]\s|#)", line):
        return False
    return bool(re.match(r"\s*[a-z(]", line)) or bool(CONNECTIVE.search(prev.rstrip()))


def ends_sentence(t):
    t = t.rstrip(" *_)”’\"")
    return bool(t) and (t[-1] in ".!?:;" or t.startswith("#"))


LIST_LABEL = re.compile(r"(?:[a-z]{1,4}|\d{1,2})\s*[.)\-]\s")             # 'a. ' 'ii. ' 'b) ' '2- '
END_WORD = re.compile(r"\b(?:of|and|or|the|to|with|in|for|a|an|by|on|at|from|as|is|are|than|that|which|if|when|"
                      r"after|before|per|without|within|including|such)$", re.I)


def stray_hash(prev, line):
    """A '#' line that Docling marked as a heading but that is the rest of the previous line -> 'sentence' | 'heading'
    | None. 'sentence': `prev` is an unfinished text line and the line starts with an all-lowercase word (p398
    '## repeat ultrasound after 5 – 7 days'), or `prev` ends on a connective word ('... when the' + '## Bishop score
    ...'), or the line starts with a number that is not a list label ('..., ## 20% die within 6 months') -> text,
    joined to that sentence. 'heading': `prev` is a long heading line (>= 60 characters, wrapped at the page width)
    and the line starts with an all-lowercase word ('## ... with hemodynamic' + '## instability') -> one heading.
    List labels ('## a. Signs', '## ii. Reperfusion'), Roman-numeral headings and capitalised headings after a list
    ending in ',' stay headings."""
    rest = re.sub(r"^\s*#+\s*", "", line)
    if not prev or LIST_LABEL.match(rest) or ROMAN_HEAD.match(line.strip()):
        return None
    w = (re.match(r"\S+", rest) or [""])[0]
    lower = bool(re.fullmatch(r"[a-z][a-z0-9\-/]*[,.:;]?", w))
    if prev.lstrip().startswith("#"):
        return "heading" if lower and len(re.sub(r"^\s*#+\s*", "", prev).strip()) >= 60 else None
    if ends_sentence(prev):
        return None
    if lower or END_WORD.search(prev.rstrip()):
        return "sentence"
    return "sentence" if re.match(r"\d", rest) and not re.match(r"\d{1,2}\s*[.)\-]\s", rest) else None


# ---------------------------------------------------------------- text fixes (stage-3 blocks, before chunking)
LATEX = re.compile(r"\$([^$\n]{1,80}?)\$")
SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
LATEX_LEFT = re.compile(r"\\[a-zA-Z]{1,12}\b|\\[!$]|\$[^$\n]{0,40}[\\^][^$\n]{0,40}\$")


def delatex(s):
    """Inline LaTeX from the OCR of image tables -> plain text. '$...$' without a backslash or '^' is left alone."""
    def conv(m):
        t = m.group(1)
        if "\\" not in t and "^" not in t:
            return m.group(0)
        t = t.replace("\\!", "")                                         # thin negative space: 4\!-\!6 -> 4-6
        t = re.sub(r"\\(?:text|mathrm)\s*\{([^}]*)\}", r"\1", t)          # \text{m} -> m
        if re.fullmatch(r"\s*\^\{?[\d\s,–-]+\}?\s*", t):                  # reference superscript ^{322-327}
            return "<sup>" + re.sub(r"[\s^{}]", "", t).replace("-", "–") + "</sup>"
        t = re.sub(r"\^\{?(\d)\}?", lambda k: k[1].translate(SUPERSCRIPT), t)   # unit power m^3 -> m³
        return re.sub(r"\s+", " ", t).strip()
    return LATEX.sub(conv, s)


def fix_text(blocks, cc):
    """Manual fixes (config chunk.text_fixes, each checked against the page image) then delatex, on every block.
    Stage 5 calls this too, so its sentence check compares the chunks with the same text.
    -> new blocks, log of changes, unused manual fixes, LaTeX-like text still left [(block, page, text)]"""
    fixes = cc.get("text_fixes") or []
    used, log_, out = collections.Counter(), [], []
    for b in blocks:
        t = b["content"]
        for i, f in enumerate(fixes):
            if b["page"] == f["page"] and f["find"] in t:
                n = t.count(f["find"])
                t = t.replace(f["find"], f["replace"])
                used[i] += n
                log_.append({"block": b["id"], "page": b["page"], "kind": "manual (page image)", "before": f["find"],
                             "after": f["replace"], "count": n, "why": f["why"]})
        for m in LATEX.finditer(t):
            new = delatex(m.group(0))
            if new != m.group(0):
                log_.append({"block": b["id"], "page": b["page"], "kind": "latex", "before": m.group(0), "after": new})
        t = delatex(t)
        out.append({**b, "content": t} if t != b["content"] else b)
    unused = [f for i, f in enumerate(fixes) if not used[i]]
    left = [(b["id"], b["page"], m.group(0)) for b in out for m in LATEX_LEFT.finditer(b["content"])]
    return out, log_, unused, left


# ---------------------------------------------------------------- score tables
def _cells(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]


def rename_score_header(text):
    """A table whose header (or first row under it) is only repeated score numbers, e.g. NEWS-2
    '| parameter | 3 | 2 | 1 | 0 | 1 | 2 | 3 |' -> one header row
    '| Physiological parameter | Score 3 (low) | Score 2 (low) | Score 1 (low) | Score 0 | Score 1 (high) | ... |'.
    -> (new text, original header lines) or None"""
    lines = text.split("\n")
    if len(lines) < 3 or not re.fullmatch(r"\|[\s|:-]*\|", lines[1].strip()):
        return None
    for r in (0, 2):
        cs = _cells(lines[r])
        nums = cs[1:]
        if len(nums) >= 4 and all(re.fullmatch(r"\d+", x) for x in nums) and len(set(nums)) < len(nums):
            zero = nums.index("0") if "0" in nums else None
            labels = [f"Score {x}" + ("" if zero is None or i == zero else " (low)" if i < zero else " (high)")
                      for i, x in enumerate(nums)]
            first = " ".join(x for x in (_cells(lines[0])[0], cs[0] if r else "") if x)
            head = "| " + " | ".join([first] + labels) + " |"
            return "\n".join([head, lines[1]] + lines[r + 1 if r else 2:]), "\n".join(lines[:r + 1])
    return None


# ---------------------------------------------------------------- regions
def assign_regions(blocks, pdf, BU, cfg, toc):
    """Split every block into pieces (block, line range) with a region:
    ('front', None) | ('chapter_title', chap) | ('section', num) | ('references', num).
    -> pieces, section_info"""
    chapters, sections = toc
    off, (fm0, fm1) = cfg["page_offset"], cfg["excluded_pages"]
    info = {}
    for num, title, printed in sections:
        h = find_heading(pdf, BU, title, printed + off)
        fixed, fixes = fix_title(title, h[1]) if h else (title, [])
        info[num] = {"number": num, "title_toc": title, "title": fixed, "title_fixes": fixes, "printed_page": printed,
                     "expected_pdf_page": printed + off, "start_page": h[0] if h else printed + off,
                     "heading_line": h[1] if h else None, "heading_ratio": round(h[2], 2) if h else None,
                     "chapter": max((c for c in chapters if c[2] <= printed), key=lambda c: c[2])[0]}
    chap_title = {c[0]: c[1] for c in chapters}
    by_page = collections.defaultdict(list)
    for i, b in enumerate(blocks):
        by_page[b["page"]].append(i)

    # switch points: (block index, line index) where a region starts
    switches = []
    for num, s in info.items():
        pos = None
        if s["heading_line"]:
            hk = letters(s["heading_line"])[:25]
            for bi in by_page.get(s["start_page"], []):
                if blocks[bi]["type"] != "text":
                    continue
                for li, line in enumerate(blocks[bi]["content"].split("\n")):
                    if hk and letters(line).startswith(hk):
                        pos = (bi, li); break
                if pos:
                    break
        s["switch_found_in_blocks"] = pos is not None
        if pos is None:                                      # fall back: the first block of the start page
            pos = (by_page[s["start_page"]][0], 0) if by_page.get(s["start_page"]) else None
        s["switch_block"] = blocks[pos[0]]["id"] if pos else None
        if pos:
            switches.append((pos, ("section", num)))
    for roman, title, printed in chapters:
        pg = printed + off
        if fm0 <= pg <= fm1 or not by_page.get(pg):
            continue
        switches.append(((by_page[pg][0], 0), ("chapter_title", roman)))
    if by_page.get(fm1 + 1):
        pass
    switches.sort()

    pieces, cur, sw = [], ("front", None), 0
    ref_seen = set()
    for bi, b in enumerate(blocks):
        lines = b["content"].split("\n") if b["type"] == "text" else [b["content"]]
        start = 0
        for li in range(len(lines)):
            new = None
            while sw < len(switches) and switches[sw][0] <= (bi, li):
                new = switches[sw][1]; sw += 1
            if new is None and cur[0] == "section" and b["type"] == "text" and is_ref_heading(lines[li], cfg):
                new = ("references", cur[1]); ref_seen.add(cur[1])
            if new is not None and new != cur:
                if li > start:
                    pieces.append((bi, start, li, cur))
                start, cur = li, new
        region = ("front", None) if b["page"] <= fm1 else cur
        pieces.append((bi, start, len(lines), region))
    for num, s in info.items():
        s["reference_heading_found"] = num in ref_seen
    return pieces, info, chap_title


def is_ref_heading(line, cfg):
    t = line.strip()
    m = re.match(r"^(#{1,4})?\s*(?:([IVXL][IVXLl]{0,5})\s*[.\-–)]\s*)?([A-Za-z]+)\s*:?\s*$", t)
    if not m or not (m.group(1) or m.group(2)):
        return False
    return difflib.SequenceMatcher(None, m.group(3).upper(), cfg["reference_heading"]).ratio() >= 0.75


# ---------------------------------------------------------------- main
class Tok:
    def __init__(self, name):
        from transformers import AutoTokenizer
        self.t = AutoTokenizer.from_pretrained(name)
        self.cache = {}

    def __call__(self, s):
        if s not in self.cache:
            self.cache[s] = len(self.t(s, add_special_tokens=False)["input_ids"])
        return self.cache[s]


def words3(s):
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def run(cfg, log):
    import pymupdf
    import build_unified as BU
    from verify_output import bare, numbers
    cc = cfg["chunk"]
    t0 = time.time()
    pdf = pymupdf.open(inp(cfg, "pdf"))
    blocks = read_jsonl(os.path.join(stage_dir(cfg, "verify"), "unified_output.verified.jsonl"))
    blocks, fix_log, unused, latex_left = fix_text(blocks, cc)
    if unused:
        raise StageFailed(f"config chunk.text_fixes not found in the text (stale?): {unused}")
    chapters, sections, toc_skipped = parse_toc(pdf, cc["toc_pages"])
    if not sections:
        raise StageFailed("no sections parsed from the TOC pages")
    pieces, info, chap_title = assign_regions(blocks, pdf, BU, cc, (chapters, sections))
    tok = Tok(cc["tokenizer"])
    layer_nums = {}

    def page_numbers(pg):
        if pg not in layer_nums:
            layer_nums[pg] = collections.Counter(x for t in numbers(BU.ref_text(pdf[pg - 1])) for x in bare(t))
        return layer_nums[pg]

    def verified(text, pages, sources):
        if not sources <= LAYER_SOURCES:
            return False
        have = collections.Counter()
        for pg in pages:
            have |= page_numbers(pg)
        return all(have[x] > 0 for t in numbers(text) for x in bare(t))

    # ---- excluded pieces + per-section item streams
    excluded, streams = [], collections.OrderedDict()
    for bi, l0, l1, region in pieces:
        b = blocks[bi]
        text = "\n".join(b["content"].split("\n")[l0:l1]) if b["type"] == "text" else b["content"]
        if not text.strip():
            continue
        kind, key = region
        if kind != "section":
            num = key if kind == "references" else None
            excluded.append({"excluded_id": f"excl_{len(excluded):05d}",
                             "reason": {"front": "front_matter", "chapter_title": "chapter_title_page",
                                        "references": "reference_list"}[kind],
                             "chapter": info[num]["chapter"] if num else (key if kind == "chapter_title" else None),
                             "section_number": num, "section_title": info[num]["title"] if num else None,
                             "pages": [b["page"]], "source_type": TYPE_MAP[b["type"]], "source": b["source"],
                             "block_ids": [b["id"]], "lines": [l0, l1] if b["type"] == "text" else None, "text": text})
            continue
        streams.setdefault(key, []).append((b, l0, l1, text))

    variants = {}
    for var in cc["variants"]:
        chunks, vstats = build_variant(var, cc, streams, info, chap_title, tok, verified)
        variants[var["name"]] = (chunks, vstats)

    out = stage_dir(cfg, "chunk")

    # ---- printed page numbers: PDF page - offset, checked against the number in each page's footer
    def footer(pg):
        page = pdf[pg - 1]
        return [int(t[4]) for t in page.get_text("blocks")
                if t[1] > 0.9 * page.rect.height and re.fullmatch(r"\s*\d{1,3}\s*", t[4])]
    idx_pages = sorted({pg for chunks, _ in variants.values() for c in chunks for pg in c["pages"]})
    foot = {pg: footer(pg) for pg in idx_pages}
    printed_check = {
        "rule": f"printed page = PDF page - {cc['page_offset']}",
        "indexed_pages": len(idx_pages),
        "pages_without_footer_number": [pg for pg in idx_pages if not foot[pg]],
        "pages_footer_disagrees": [{"pdf_page": pg, "printed_by_rule": pg - cc["page_offset"], "footer": foot[pg]}
                                   for pg in idx_pages if foot[pg] and pg - cc["page_offset"] not in foot[pg]],
        "chunks_without_printed_page": {n: [c["chunk_id"] for c in ch if not c["metadata"].get("printed_pages")]
                                        for n, (ch, _) in variants.items()}}

    # ---- document errata (errors in the guideline itself): tag chunks, text unchanged
    errata = []
    for e in cc.get("errata") or []:
        rx = [(m["page"], re.compile(m["regex"], re.I)) for m in e["match"]]
        hits = {n: [c["chunk_id"] for c in ch if any(pg in c["pages"] and r.search(c["text_en"]) for pg, r in rx)]
                for n, (ch, _) in variants.items()}
        for n, (ch, _) in variants.items():
            for c in ch:
                if c["chunk_id"] in hits[n]:
                    c["metadata"].setdefault("errata", []).append(e["id"])
        errata.append({k: v for k, v in e.items() if k != "match"} | {"chunks": hits})
        if not all(hits.values()):
            raise StageFailed(f"erratum {e['id']}: no chunk matched in some variant {hits}")
    write_json(os.path.join(p(cfg["output_root"]), "errata.json"),
               {"note": "Errors in the source document itself, not pipeline errors. The chunk text is NOT changed; "
                        "chunks that contain an erratum carry metadata.errata = [id].", "errata": errata})

    # ---- tables whose numbers could not be checked against the text layer (pictures in the PDF): manual review
    with open(os.path.join(p(cfg["output_root"]), "manual_review_tables.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["page", "chunk_id", "variant", "printed_page"])
        for n, (ch, _) in variants.items():
            for c in ch:
                if c["source_type"] == "table" and not c["numbers_verified"]:
                    for pg in c["pages"]:
                        w.writerow([pg, c["chunk_id"], n, pg - cc["page_offset"]])

    for name, (chunks, _) in variants.items():
        write_jsonl(os.path.join(out, f"chunks_{name}.jsonl"), chunks)
    write_jsonl(os.path.join(out, "excluded.jsonl"), excluded)
    write_json(os.path.join(out, "text_fixes.json"), {"changes": fix_log, "latex_like_text_left": latex_left})
    stray = next(iter(variants.values()))[1]["stray_hash_lines"]
    write_json(os.path.join(out, "stray_headings.json"),
               {"rule": stray_hash.__doc__.split("\n")[0], "count": len(stray), "lines": stray})

    # ---- section report: TOC, start pages, mapping of the stage-2 labels
    assigned = {}
    for bi, l0, l1, region in pieces:
        assigned.setdefault(blocks[bi]["id"], set()).add(region)
    labels = collections.defaultdict(lambda: collections.Counter())
    for b in blocks:
        lab = f"{b['section_number'] or '-'} {b['section']}"
        for r in assigned.get(b["id"], {("front", None)}):
            labels[lab][f"{r[0]}:{r[1]}" if r[1] is not None else r[0]] += 1
    mapping = []
    for lab, cnt in labels.items():
        n = lab.split(" ", 1)[0]
        num = int(n) if n.isdigit() else None
        toc_entry = info.get(num)
        mapping.append({"stage2_label": lab, "toc_section": num if toc_entry else None,
                        "toc_title": toc_entry["title"] if toc_entry else None,
                        "blocks_by_toc_region": dict(cnt),
                        "agrees": bool(toc_entry) and all(k.split(":")[1] == str(num) for k in cnt if ":" in k)})
    dl = json.load(open(inp(cfg, "docling_json")))
    heads = [(t["prov"][0]["page_no"], t["text"]) for t in dl["texts"] if t["label"] == "section_header" and t.get("prov")]
    dl_map, dl_unplaced = [], []
    for pg, h in heads:
        hk = letters(h)
        best = max(info.values(), key=lambda s: difflib.SequenceMatcher(None, letters(s["title_toc"])[:30], hk[:30]).ratio())
        r = difflib.SequenceMatcher(None, letters(best["title_toc"])[:30], hk[:30]).ratio()
        if r >= 0.8 and len(hk) >= 6:
            dl_map.append({"page": pg, "heading": h, "toc_section": best["number"], "ratio": round(r, 2),
                           "on_start_page": pg == best["start_page"]})
    sec_report = {
        "toc_pages": cc["toc_pages"], "chapters": [{"chapter": c, "title": t, "printed_page": pp,
                                                    "pdf_page": pp + cc["page_offset"]} for c, t, pp in chapters],
        "sections_in_toc": len(sections),
        "sections_per_chapter": dict(collections.Counter(s["chapter"] for s in info.values())),
        "toc_lines_not_sections": toc_skipped,
        "sections": list(info.values()),
        "sections_heading_not_found": [n for n, s in info.items() if not s["heading_line"]],
        "sections_start_not_at_expected_page": [(n, s["expected_pdf_page"], s["start_page"]) for n, s in info.items()
                                                if s["start_page"] != s["expected_pdf_page"]],
        "sections_without_reference_heading": [n for n, s in info.items() if not s["reference_heading_found"]],
        "title_fixes": {n: s["title_fixes"] for n, s in info.items() if s["title_fixes"]},
        "stage2_labels": len(labels), "stage2_label_mapping": sorted(mapping, key=lambda m: (m["toc_section"] or 0)),
        "stage2_labels_not_in_toc": [m["stage2_label"] for m in mapping if not m["toc_section"]],
        "stage2_labels_disagreeing": [m for m in mapping if m["toc_section"] and not m["agrees"]],
        "docling_section_headers": len(heads),
        "docling_headers_matching_a_toc_title": dl_map,
        "toc_sections_without_docling_header": sorted(set(info) - {m["toc_section"] for m in dl_map}),
    }
    write_json(os.path.join(out, "sections.json"), sec_report)
    stats = {name: vs for name, (_, vs) in variants.items()}
    stats["excluded"] = dict(collections.Counter(e["reason"] for e in excluded))
    stats["excluded_records"] = len(excluded)
    stats["printed_pages"] = printed_check
    stats["text_fixes"] = {"changes": len(fix_log), "latex_like_text_left": len(latex_left)}
    write_json(os.path.join(out, "chunk_stats.json"), stats)
    for name, (chunks, vs) in variants.items():
        log(f"variant {name}: {len(chunks)} chunks {vs['per_source_type']} tokens {vs['tokens']}; "
            f"tiny merged {vs['tiny_merged']}, left {len(vs['tiny_left'])}")
    log(f"TOC: {len(sections)} sections in {len(chapters)} chapters; excluded {stats['excluded']}")
    log(f"text fixes {len(fix_log)} (LaTeX-like left {len(latex_left)}); stray '#' lines {len(stray)}; "
        f"errata {[(e['id'], {n: len(v) for n, v in e['chunks'].items()}) for e in errata]}; printed pages: "
        f"no footer {printed_check['pages_without_footer_number']}, footer disagrees {printed_check['pages_footer_disagrees']}")
    skip = {"flowchart_pairs", "stray_hash_lines"}
    return {"toc_sections": len(sections), "chapters": len(chapters), "excluded": stats["excluded"],
            "text_fixes": stats["text_fixes"], "stray_hash_lines": len(stray), "printed_pages": printed_check,
            "errata": {e["id"]: e["chunks"] for e in errata},
            "variants": {n: {"chunks": len(c), **{k: v for k, v in vs.items() if k not in skip}}
                         for n, (c, vs) in variants.items()}, "seconds": round(time.time() - t0, 1)}


def citation(ch, num, title, pages, offset):
    """'Ch. I §3 Early Warning Score in Hospital, p. 30': the PRINTED page (PDF page - offset), the page number a
    reader of the printed guideline sees. The chunk's `pages` keep the PDF page (for the page image)."""
    pr = [pg - offset for pg in pages]
    return f"Ch. {ch} §{num} {title}, " + (f"p. {pr[0]}" if len(pr) == 1 else f"pp. {pr[0]}–{pr[-1]}")


def merge_tiny(chunks, cc, tok, stats):
    """Each chunk under min_tokens_flag (and a run of them) goes in front of the next chunk of the same section.
    The merged chunk keeps the next chunk's id and type; metadata.merged_from lists what was merged in."""
    mn, out, pending, left = cc["min_tokens_flag"], [], [], []

    def merge(small, c):
        sep = "\n" if c["source_type"] == "body_text" else "\n\n"
        text = sep.join([x["text_en"] for x in small] + [c["text_en"]])
        assert c["embed_text_en"].endswith(c["text_en"])
        emb = c["embed_text_en"][:len(c["embed_text_en"]) - len(c["text_en"])] + text
        pages = sorted({pg for x in small + [c] for pg in x["pages"]})
        m = dict(c["metadata"])
        alts = [x["metadata"]["alt_description"] for x in small + [c] if x["metadata"].get("alt_description")]
        if alts:                                                 # a paired Qwen3 description of a merged flowchart
            m["alt_description"] = "\n\n".join(alts)
        m.update(printed_pages=[pg - cc["page_offset"] for pg in pages], embed_tokens=tok(emb),
                 merged_from=[{"chunk_id": x["chunk_id"], "source_type": x["source_type"], "tokens": x["tokens"],
                               "pages": x["pages"]} for x in small])
        return {**c, "pages": pages, "text_en": text, "embed_text_en": emb, "tokens": tok(text),
                "citation": citation(c["chapter"], c["section_number"], c["section_title"], pages, cc["page_offset"]),
                "source": "+".join(sorted({s for x in small + [c] for s in x["source"].split("+")})),
                "block_ids": list(dict.fromkeys(b for x in small + [c] for b in x["block_ids"])),
                "numbers_verified": all(x["numbers_verified"] for x in small + [c]), "metadata": m}

    for c in chunks:
        if pending and pending[0]["section_number"] != c["section_number"]:
            out += pending; left += pending; pending = []        # never merge across a section
        if c["tokens"] < mn:
            pending.append(c); continue
        if pending:
            stats["tiny_merged"] += len(pending)
            c = merge(pending, c); pending = []
        out.append(c)
    out += pending; left += pending
    return out, [{"chunk_id": x["chunk_id"], "tokens": x["tokens"], "reason": "last chunk of its section"} for x in left]


def build_variant(var, cc, streams, info, chap_title, tok, verified):
    target, mx = var["target"], var["max"]
    ovl_budget = cc["overlap"] * target
    chunks, stats = [], collections.Counter()
    pairs, stray = [], []

    for num, items in streams.items():
        s = info[num]
        ch = s["chapter"]
        slug = f"s{num:02d}_{slugify(s['title'])}"
        seq = [0]

        def emit(stype, text, units_meta, extra, sources, verified_flag=None):
            pages = sorted({p for u in units_meta for p in u["pages"]})
            bids = list(dict.fromkeys(b for u in units_meta for b in u["block_ids"]))
            subs = list(dict.fromkeys(u["subsection"] for u in units_meta if u.get("subsection") and not u.get("overlap")))
            sub = "; ".join(subs) if subs else None
            seq[0] += 1
            crumb = f"Chapter {ch} {chap_title.get(ch, '')} > {num}. {s['title']}" + (f" > {sub}" if sub else "")
            cite = citation(ch, num, s["title"], pages, cc["page_offset"])
            emb = crumb + "\n" + (extra.pop("_embed_prefix", "") or "") + text
            srcs = sorted(sources)
            nv = verified(text, pages, set(srcs)) if verified_flag is None else verified_flag
            c = {"chunk_id": f"{slug}_{seq[0]:04d}", "chapter": ch, "section_number": num, "section_title": s["title"],
                 "subsection": sub, "pages": pages, "source_type": stype, "text_en": text,
                 "text_km": None, "text_lo": None, "text_vi": None, "embed_text_en": emb, "citation": cite,
                 "source": "+".join(srcs), "block_ids": bids, "tokens": tok(text), "numbers_verified": nv,
                 "metadata": {"variant": var["name"], "chapter_title": chap_title.get(ch), "printed_pages":
                              [p - cc["page_offset"] for p in pages], "subsections": subs,
                              "embed_tokens": tok(emb), **extra}}
            chunks.append(c)
            stats[f"type_{stype}"] += 1
            return c

        # ---- build the item stream: sentence units and atoms
        stream, sub, last_unit = [], None, None
        algos = [(b, t) for b, _, _, t in items if b["type"] == "algorithm"]
        images = {b["id"]: (b, t) for b, _, _, t in items if b["type"] == "image"}
        paired = {}                                          # image id -> algorithm id
        for a, at in algos:
            if len(at) < cc["flowchart_min_chars"]:
                continue
            aw = words3(at)
            cand = [(len(aw & words3(it)) / max(1, len(aw)), iid) for iid, (ib, it) in images.items()
                    if ib["page"] == a["page"] and iid not in paired]
            if cand:
                sc, iid = max(cand)
                if sc >= cc["flowchart_match_min"]:
                    paired[iid] = a["id"]
                    pairs.append({"algorithm": a["id"], "image": iid, "page": a["page"], "overlap": round(sc, 2)})
        alg_of = {v: k for k, v in paired.items()}
        prev_text_line = None
        for b, l0, l1, text in items:
            base = {"block_ids": [b["id"]], "pages": [b["page"]], "source": b["source"]}
            if b["type"] == "text" and not b["metadata"].get("in_figure"):
                for li, line in enumerate(text.split("\n")):
                    if not line.strip():
                        continue
                    sk = stray_hash(prev_text_line, line) if line.lstrip().startswith("#") else None
                    if sk:
                        stray.append({"page": b["page"], "block": b["id"], "section": num, "fixed_as": sk,
                                      "previous_line": prev_text_line.strip()[-80:], "line": line.strip()})
                        rest = re.sub(r"^\s*#+\s*", "", line)
                        if sk == "heading" and last_unit is not None and last_unit["kind"] == "heading":
                            last_unit["text"] += " " + rest                 # second line of a wrapped heading
                            prev_text_line = line
                            continue
                        line = rest                                     # text, joined to the sentence it continues
                    if line.lstrip().startswith("#"):
                        m = ROMAN_HEAD.match(line.strip())
                        if m:
                            sub = f"{m.group(1).replace('l', 'I')}. {m.group(2).strip()}"
                        u = {**base, "text": line.strip(), "kind": "heading", "nl": True, "subsection": sub,
                             "roman": bool(m)}
                        stream.append(("unit", u)); last_unit = u
                        prev_text_line = line
                        continue
                    sents = split_sentences(line.strip())
                    for si, st in enumerate(sents):
                        u = {**base, "text": st, "kind": "sent", "nl": si == 0, "subsection": sub}
                        if si == 0 and last_unit is not None and last_unit["kind"] == "sent" and \
                                continues(last_unit["text"], line):
                            # the sentence continues from the previous line / block / page: one unit
                            last_unit["text"] += " " + st
                            if last_unit["block_ids"][-1] != b["id"]:
                                last_unit["block_ids"] = last_unit["block_ids"] + [b["id"]]
                                last_unit["pages"] = sorted(set(last_unit["pages"] + [b["page"]]))
                                stats["sentences_joined_across_blocks"] += 1
                            else:
                                stats["sentences_joined_across_lines"] += 1
                            continue
                        stream.append(("unit", u)); last_unit = u
                    prev_text_line = line
                continue
            # atoms
            if b["type"] == "image" and b["id"] in paired:
                continue                                       # emitted with its algorithm
            atom = {**base, "type": b["type"], "text": text, "block": b, "subsection": sub,
                    "caption": prev_text_line if prev_text_line and re.match(
                        r"^\W*(Table|Tab\.|Figure|Fig\.|Algorithm|Diagram)\s*\(?\d", prev_text_line.strip(), re.I) else None}
            if b["type"] == "algorithm" and b["id"] in alg_of:
                ib, it = images[alg_of[b["id"]]]
                atom["alt"] = (ib, it)
            stream.append(("atom", atom))

        # ---- pack
        cur = []

        def tokens_of(us):
            return sum(tok(u["text"]) for u in us)

        def flush(carry):
            nonlocal cur
            body = [u for u in cur if not u.get("overlap")]
            if not body:
                cur = []
                return
            moved = []
            if carry:                                        # never end on a heading: move it to the next chunk
                while cur and cur[-1]["kind"] == "heading" and len(cur) > 1:
                    moved.insert(0, cur.pop())
            text = ""
            for i, u in enumerate(cur):
                text += (("\n" if u["nl"] else " ") if i else "") + u["text"]
            sources = {u["source"] for u in cur}
            ov = [u for u in cur if u.get("overlap")]
            extra = {"overlap_tokens": tokens_of(ov) if ov else 0}
            if any(u.get("forced_split") for u in cur):
                extra["forced_split"] = True
            emit("body_text", text, cur, extra, sources)
            nxt = []
            if carry:
                # trailing whole sentences whose total is closest to the budget (at most 2x the budget)
                tail, tsum, best = [], 0, []
                for u in reversed(cur):
                    if u is cur[0] or u["kind"] != "sent" or u.get("forced_split") or tsum + tok(u["text"]) > 2 * ovl_budget:
                        break
                    tail.insert(0, u); tsum += tok(u["text"])
                    if not best or abs(tsum - ovl_budget) < abs(tokens_of(best) - ovl_budget):
                        best = list(tail)
                tail = best
                if tail and tail[-1] is cur[-1]:
                    nxt = [{**u, "overlap": True, "nl": u["nl"]} for u in tail]
                    stats["overlaps"] += 1
                else:
                    stats["overlap_skipped_long_sentence"] += 1
            cur = nxt + moved

        for kind, it in stream:
            if kind == "atom":
                body = [u for u in cur if not u.get("overlap")]
                if body and ends_sentence(body[-1]["text"]):
                    flush(carry=False)
                elif not body:
                    cur = []
                emit_atom(it, emit, tok, target, mx, stats)
                continue
            u = it
            ut = tok(u["text"])
            body_tok = tokens_of([x for x in cur if not x.get("overlap")])
            if u["kind"] == "heading" and u.get("roman") and body_tok >= 0.4 * target:
                flush(carry=False)
            elif cur and body_tok and tokens_of(cur) + ut > target and \
                    not (body_tok < 0.5 * target and tokens_of(cur) + ut <= mx):
                flush(carry=True)
            if ut > mx:                                      # one sentence longer than max: cut at ; , or spaces
                flush(carry=False)
                for piece in cut_sentence(u["text"], tok, target):
                    cur = [{**u, "text": piece, "forced_split": True, "nl": not cur}]
                    flush(carry=False)
                stats["forced_split_sentences"] += 1
                continue
            cur.append(u)
        flush(carry=False)

    under = sum(1 for c in chunks if c["tokens"] < cc["min_tokens_flag"])
    chunks, tiny_left = merge_tiny(chunks, cc, tok, stats)
    toks = [c["tokens"] for c in chunks]
    per_type = collections.Counter(c["source_type"] for c in chunks)
    tk = {t: [c["tokens"] for c in chunks if c["source_type"] == t] for t in per_type}
    ov = [c["metadata"]["overlap_tokens"] / c["tokens"] for c in chunks if c["metadata"].get("overlap_tokens")]
    text_n = sum(1 for c in chunks if c["source_type"] == "body_text")
    return chunks, {"chunks": len(chunks), "per_source_type": dict(per_type),
                    "tokens": {"min": min(toks), "median": statistics.median(toks), "max": max(toks)},
                    "tokens_per_type": {t: {"min": min(v), "median": statistics.median(v), "max": max(v)} for t, v in tk.items()},
                    "over_max": sum(1 for c in chunks if c["tokens"] > mx),
                    "over_max_by_type": dict(collections.Counter(c["source_type"] for c in chunks if c["tokens"] > mx)),
                    "mean_overlap_fraction": round(statistics.mean(ov), 3) if ov else 0,
                    "text_chunks_with_overlap": f"{len(ov)}/{text_n}",
                    "tiny_before_merge": under, "tiny_merged": stats["tiny_merged"], "tiny_left": tiny_left,
                    "flowchart_pairs": pairs, "stray_hash_lines": stray, "counters": dict(stats)}


def cut_sentence(text, tok, target):
    parts = re.split(r"(?<=;)\s+|(?<=,)\s+", text)
    if max(tok(p) for p in parts) > target:
        parts = text.split(" ")
    out, cur = [], ""
    for p_ in parts:
        cand = f"{cur} {p_}".strip()
        if cur and tok(cand) > target:
            out.append(cur); cur = p_
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def pack_paragraphs(text, tok, target):
    """A long Qwen3 description -> parts of whole paragraphs (whole sentences if a paragraph is too long)."""
    units = []
    for para in re.split(r"\n\s*\n", text):
        if not para.strip():
            continue
        if tok(para) <= target:
            units.append(para.strip())
        else:
            units += [s for line in para.split("\n") for s in (split_sentences(line.strip()) or [])]
    out, cur = [], ""
    for u in units:
        cand = f"{cur}\n\n{u}" if cur else u
        if cur and tok(cand) > target:
            out.append(cur); cur = u
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def emit_atom(a, emit, tok, target, mx, stats):
    b = a["block"]
    meta = {"subsection_at": a["subsection"]}
    if a.get("caption"):
        meta["caption"] = a["caption"].strip("# ")
        meta["_embed_prefix"] = a["caption"].strip("# ") + "\n"
    um = [{"block_ids": a["block_ids"], "pages": a["pages"], "subsection": a["subsection"]}]
    for k in ("original_text", "original_language", "translation_flags", "machine_translation"):
        if k in b["metadata"]:
            meta[k] = b["metadata"][k]
    if b["type"] == "algorithm":
        if a.get("alt"):
            ib, it = a["alt"]
            meta.update(alt_description=it, picture_ref=ib["metadata"].get("picture_ref"),
                        image_path=ib["metadata"].get("image_path"), alt_source=ib["source"])
            um.append({"block_ids": [ib["id"]], "pages": [ib["page"]], "subsection": a["subsection"]})
            stats["flowcharts_paired_with_qwen3"] += 1
        emit("flowchart", a["text"], um, meta, {b["source"]})
        return
    if b["type"] == "image":
        meta.update({k: b["metadata"].get(k) for k in ("picture_ref", "image_path", "image_type")})
        parts = [a["text"]] if tok(a["text"]) <= mx else pack_paragraphs(a["text"], tok, target)
        for i, t in enumerate(parts):
            m = dict(meta, figure_part=i + 1, figure_parts=len(parts)) if len(parts) > 1 else meta
            emit("figure", t, um, m, {b["source"]}, verified_flag=False)
        if len(parts) > 1:
            stats["figures_split"] += 1
        return
    if b["type"] == "text":                                  # text-layer words inside a picture
        meta["in_figure"] = b["metadata"].get("in_figure")
        emit("figure", a["text"], um, meta, {b["source"]})
        return
    # table
    renamed = rename_score_header(a["text"])
    if renamed:
        a = dict(a, text=renamed[0])
        meta["original_header"] = renamed[1]
        stats["score_headers_renamed"] += 1
    lines = a["text"].split("\n")
    if tok(a["text"]) <= mx or len(lines) < 4 or not re.fullmatch(r"\|[\s|:-]*\|", lines[1].strip()):
        emit("table", a["text"], um, meta, {b["source"]})
        return
    head, rows = lines[:2], lines[2:]
    parts, cur = [], []
    ht = tok("\n".join(head))
    for r in rows:
        if cur and ht + tok("\n".join(cur + [r])) > target:
            parts.append(cur); cur = []
        cur.append(r)
    if cur:
        parts.append(cur)
    for i, rs in enumerate(parts):
        m = dict(meta, table_part=i + 1, table_parts=len(parts), header_repeated=i > 0,
                 table_header="\n".join(head))
        if "_embed_prefix" in meta and i:
            m["_embed_prefix"] = meta["_embed_prefix"]
        emit("table", "\n".join(head + rs), um, m, {b["source"]})
    stats["tables_split"] += 1
