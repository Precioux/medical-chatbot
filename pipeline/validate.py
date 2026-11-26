"""Stage 5: checks on the chunks of both variants + chunks_preview.html.

 1 numbers & symbols: the stage-3 check run on the chunks. (a) chunks + excluded.jsonl against every page: must
   give expected_numbers / expected_symbols. (b) the index alone: pages after the front matter, reference with the
   excluded text (reference lists, chapter title page) taken out: nothing may be missing.
   A chunk's text counts for every page it lists.
 2 every block of the verified unified output is in a chunk or in excluded.jsonl; every sentence of it as well
 3 no chunk crosses a section; every table part starts with the table's header
 4 every citation matches the chunk's chapter, section and pages
 5 token histogram per source_type; chunks under min_tokens_flag listed
 6 chunks_preview.html: random chunks + all chunks of the preview pages, next to the page image
Outputs (stage5_validate/): validation.json, chunks_preview.html
"""
import base64, collections, html, io, json, os, random, re, time

from pipeline.common import StageFailed, inp, read_jsonl, stage_dir, write_json

BINS = [0, 40, 64, 128, 192, 256, 384, 512, 768, 1024, 10 ** 9]


def key(s):
    return re.sub(r"\s+", "", s).lower()


def run(cfg, log):
    import pymupdf
    import verify_output as V
    from pipeline.chunk import split_sentences
    V.PDF, V.DOCLING, V.PAGES = inp(cfg, "pdf"), inp(cfg, "docling_json"), inp(cfg, "page_images")
    t0 = time.time()
    cdir, out = stage_dir(cfg, "chunk"), stage_dir(cfg, "validate")
    doc = pymupdf.open(inp(cfg, "pdf"))
    dl = json.load(open(inp(cfg, "docling_json")))
    blocks = read_jsonl(os.path.join(stage_dir(cfg, "verify"), "unified_output.verified.jsonl"))
    bidx = {b["id"]: i for i, b in enumerate(blocks)}
    excluded = read_jsonl(os.path.join(cdir, "excluded.jsonl"))
    secs = json.load(open(os.path.join(cdir, "sections.json")))
    sinfo = {s["number"]: s for s in secs["sections"]}
    fm1 = cfg["chunk"]["excluded_pages"][1]
    exp_n, exp_s = cfg["verify"]["expected_numbers"], cfg["verify"]["expected_symbols"]
    res, failures = {}, []

    excl_by_page = collections.defaultdict(list)
    for e in excluded:
        for pg in e["pages"]:
            excl_by_page[pg].append({"content": e["text"], "type": e["source_type"]})

    for var in cfg["chunk"]["variants"]:
        name, mx = var["name"], var["max"]
        chunks = read_jsonl(os.path.join(cdir, f"chunks_{name}.jsonl"))
        r = {"chunks": len(chunks)}
        # ---- 1 numbers & symbols
        by_page = collections.defaultdict(list)
        for c in chunks:
            for pg in c["pages"]:
                by_page[pg].append({"content": c["text_en"], "type": c["source_type"]})
        allp = collections.defaultdict(list, {pg: by_page[pg] + excl_by_page[pg] for pg in set(by_page) | set(excl_by_page)})
        _, tot, _, _, miss_pages = V.coverage(doc, allp, dl)
        a = {"numbers": f"{tot['nums_value']}/{tot['nums_ref']}", "numbers_exact": f"{tot['nums_exact']}/{tot['nums_ref']}",
             "symbols": f"{tot['sym_ref'] - tot['sym_missing']}/{tot['sym_ref']}", "pages_missing_numbers": miss_pages,
             "word_coverage": round(tot["words_found"] / max(1, tot["words_ref"]), 4)}
        ok_a = tot["nums_ref"] == tot["nums_value"] == exp_n and tot["sym_ref"] == exp_s and tot["sym_missing"] == 0
        idx_pages = set(range(fm1 + 1, doc.page_count + 1))
        ref_minus = {pg: "\n".join(e["content"] for e in excl_by_page[pg]) for pg in idx_pages if excl_by_page.get(pg)}
        pages_b, totb, _, _, miss_b = V.coverage(doc, by_page, dl, pages_subset=idx_pages, ref_minus=ref_minus)
        b_ = {"numbers": f"{totb['nums_value']}/{totb['nums_ref']}", "numbers_exact": f"{totb['nums_exact']}/{totb['nums_ref']}",
              "symbols": f"{totb['sym_ref'] - totb['sym_missing']}/{totb['sym_ref']}", "pages_missing_numbers": miss_b,
              "missing": {pg: pages_b[pg]["numbers_missing"] for pg in miss_b},
              "symbols_missing": {pg: p["symbols_missing"] for pg, p in pages_b.items() if p.get("symbols_missing")}}
        ok_b = totb["nums_ref"] == totb["nums_value"] and totb["sym_missing"] == 0
        r["numbers_symbols"] = {"chunks_plus_excluded_all_pages": a, "index_only_pages_%d_%d" % (fm1 + 1, doc.page_count): b_,
                                "pass": ok_a and ok_b}
        if not r["numbers_symbols"]["pass"]:
            failures.append(f"{name}: numbers/symbols {a['numbers']} {a['symbols']} | index {b_['numbers']} {b_['symbols']}")

        # ---- 2 orphans
        refs = collections.defaultdict(list)
        for c in chunks:
            for bid in c["block_ids"]:
                refs[bid].append(c["text_en"])
                if c["metadata"].get("alt_description"):      # paired Qwen3 image block -> kept as alt text
                    refs[bid].append(c["metadata"]["alt_description"])
        for e in excluded:
            for bid in e["block_ids"]:
                refs[bid].append(e["text"])
        orphans = [b["id"] for b in blocks if b["id"] not in refs]
        lost = []
        for b in blocks:
            if b["id"] not in refs:
                continue
            have = key("\n".join(refs[b["id"]]))
            words = collections.Counter(re.findall(r"\w+", " ".join(refs[b["id"]]).lower()))
            for line in b["content"].split("\n"):
                for snt in split_sentences(line.strip()) if line.strip() else []:
                    if key(snt) in have:
                        continue
                    w = re.findall(r"\w+", snt.lower())          # forced splits / header repeats: words present
                    if w and all(words[x] for x in w):
                        continue
                    lost.append({"block": b["id"], "page": b["page"], "sentence": snt[:160]})
        r["orphans"] = {"blocks_not_in_chunks_or_excluded": orphans, "sentences_not_found": lost[:50],
                        "sentences_not_found_count": len(lost), "pass": not orphans and not lost}
        if orphans or lost:
            failures.append(f"{name}: {len(orphans)} orphan blocks, {len(lost)} lost sentences")

        # ---- 3 sections + table headers
        starts = sorted((bidx[s["switch_block"]], n) for n, s in sinfo.items() if s.get("switch_block"))

        def sections_of(bid):
            i = bidx[bid]
            prev = [n for j, n in starts if j <= i]
            on = [n for j, n in starts if j == i]
            cur = prev[-1] if prev else None
            return {cur} | ({prev[-2]} if on and len(prev) > 1 else set())   # a block holding a section start
        crossing = []
        for c in chunks:
            ok = all(c["section_number"] in sections_of(bid) for bid in c["block_ids"])
            s, nxt = sinfo[c["section_number"]], sinfo.get(c["section_number"] + 1)
            ok &= c["pages"][0] >= s["start_page"] and (nxt is None or c["pages"][-1] <= nxt["start_page"])
            if not ok:
                crossing.append(c["chunk_id"])
        bad_tables = []
        for c in chunks:
            if c["source_type"] != "table":
                continue
            lines = c["text_en"].split("\n")
            h = c["metadata"].get("table_header")
            if h and "\n".join(lines[:2]) != h:
                bad_tables.append(c["chunk_id"])
            elif c["metadata"].get("table_part") and not (len(lines) > 2 and re.fullmatch(r"\|[\s|:-]*\|", lines[1].strip())):
                bad_tables.append(c["chunk_id"])
        r["sections"] = {"chunks_crossing_a_section": crossing, "table_parts_without_header": bad_tables,
                         "tables_split": len({c["block_ids"][0] for c in chunks if c["metadata"].get("table_part")}),
                         "pass": not crossing and not bad_tables}
        if crossing or bad_tables:
            failures.append(f"{name}: {len(crossing)} chunks cross a section, {len(bad_tables)} table parts lack the header")

        # ---- 4 citations
        bad_cite = []
        for c in chunks:
            m = re.fullmatch(r"Ch\. (\w+) §(\d+) (.+), (?:p\. (\d+)|pp\. (\d+)–(\d+))", c["citation"])
            ok = bool(m) and m[1] == c["chapter"] and int(m[2]) == c["section_number"] and m[3] == c["section_title"] \
                and sinfo[c["section_number"]]["chapter"] == c["chapter"] and sinfo[c["section_number"]]["title"] == c["section_title"]
            if ok:
                ok = (int(m[4]) == c["pages"][0] and len(c["pages"]) == 1) if m[4] else \
                    (int(m[5]) == c["pages"][0] and int(m[6]) == c["pages"][-1])
            if not ok:
                bad_cite.append((c["chunk_id"], c["citation"], c["pages"]))
        r["citations"] = {"bad": bad_cite, "pass": not bad_cite}
        if bad_cite:
            failures.append(f"{name}: {len(bad_cite)} citations do not match")

        # ---- 5 tokens
        hist = {}
        for t in sorted({c["source_type"] for c in chunks}):
            v = [c["tokens"] for c in chunks if c["source_type"] == t]
            hist[t] = {f"{BINS[i]}-{BINS[i + 1] - 1 if BINS[i + 1] < 10 ** 9 else ''}": sum(BINS[i] <= x < BINS[i + 1] for x in v)
                       for i in range(len(BINS) - 1)}
        small = [(c["chunk_id"], c["source_type"], c["tokens"], c["text_en"][:80]) for c in chunks
                 if c["tokens"] < cfg["chunk"]["min_tokens_flag"]]
        over = [(c["chunk_id"], c["source_type"], c["tokens"]) for c in chunks if c["tokens"] > mx]
        r["tokens"] = {"histogram": hist, "under_min": small, "under_min_count": len(small),
                       "under_min_by_type": dict(collections.Counter(s[1] for s in small)),
                       "over_max": over, "over_max_by_type": dict(collections.Counter(o[1] for o in over)),
                       "numbers_verified": dict(collections.Counter(f"{c['source_type']}:{c['numbers_verified']}" for c in chunks))}
        res[name] = r
        log(f"variant {name}: {len(chunks)} chunks; numbers {a['numbers']} symbols {a['symbols']} | index "
            f"{b_['numbers']} {b_['symbols']}; orphans {len(orphans)}/{len(lost)}; crossing {len(crossing)}; "
            f"bad tables {len(bad_tables)}; bad citations {len(bad_cite)}; <{cfg['chunk']['min_tokens_flag']} tok {len(small)}")

    preview(cfg, out, doc)
    res["seconds"] = round(time.time() - t0, 1)
    res["failures"] = failures
    write_json(os.path.join(out, "validation.json"), res)
    if failures:
        raise StageFailed("; ".join(failures))
    return {k: v for k, v in res.items()}


# ---------------------------------------------------------------- 6 preview
def page_img(cfg, pno):
    from PIL import Image
    img = Image.open(os.path.join(inp(cfg, "page_images"), f"page_{pno:04d}.png")).convert("RGB")
    img.thumbnail((900, 1300))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=65)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def preview(cfg, out, doc):
    vc = cfg["validate"]
    cdir = stage_dir(cfg, "chunk")
    want_pages = vc["preview_pages"]
    sections, imgs = [], {}
    for var in cfg["chunk"]["variants"]:
        chunks = read_jsonl(os.path.join(cdir, f"chunks_{var['name']}.jsonl"))
        rng = random.Random(vc["seed"])
        rand = rng.sample(chunks, min(vc["random_chunks"], len(chunks)))
        groups = [(f"Page {pg}", pg, [c for c in chunks if pg in c["pages"]]) for pg in want_pages]
        groups += [(f"Random {i + 1}: {c['chunk_id']}", c["pages"][0], [c]) for i, c in enumerate(rand)]
        for _, pg, _ in groups:
            imgs.setdefault(pg, None)
        sections.append((var, groups))
    for pg in imgs:
        imgs[pg] = page_img(cfg, pg)
    css = """
:root{--bg:#fff;--fg:#1d1d1f;--muted:#666;--card:#f6f6f7;--line:#ddd;--chip:#e8eef9;--acc:#2f5fb3;--warn:#a15c00;--warnbg:#fff3e0}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161618;--fg:#e9e9ea;--muted:#9a9a9f;--card:#202023;--line:#333;--chip:#24324a;--acc:#8fb0ff;--warn:#ffb74d;--warnbg:#3a2a12}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:17px;margin:0 0 8px} .muted{color:var(--muted)}
.tabs{display:flex;gap:8px;margin:12px 0} .tabs button{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:6px 12px;border-radius:6px;cursor:pointer}
.tabs button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
nav{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px} nav a{background:var(--chip);color:var(--fg);padding:3px 8px;border-radius:6px;text-decoration:none;font-size:12px}
section{border-top:1px solid var(--line);padding:16px 0}
.row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:16px}
@media (max-width:900px){.row{grid-template-columns:1fr}}
img{width:100%;height:auto;border:1px solid var(--line);border-radius:4px;position:sticky;top:8px}
.ch{background:var(--card);border-radius:6px;padding:8px 10px;margin:0 0 10px}
.ch pre{white-space:pre-wrap;word-break:break-word;font:12.5px/1.45 ui-monospace,monospace;margin:6px 0 0}
.meta{font-size:12px;color:var(--muted)} .meta b{color:var(--fg)}
.flag{display:inline-block;font-size:11px;padding:0 6px;border-radius:4px;background:var(--warnbg);color:var(--warn);margin-left:4px}
details summary{cursor:pointer;color:var(--muted);font-size:12px}"""
    parts = ["<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
             f"<title>Chunk Preview Sheet</title><style>{css}</style></head><body><h1>Chunk preview</h1>"
             "<div class=muted>Each group shows the PDF page (left) and the chunks that cite it (right): all chunks of pages "
             f"{', '.join(map(str, want_pages))}, then {vc['random_chunks']} random chunks per variant. "
             "Chunks list type, tokens, citation and whether their numbers were verified against the text layer.</div>"
             "<div class=tabs>" + "".join(f"<button data-v='{v['name']}'>{v['name']} tokens (max {v['max']})</button>"
                                          for v, _ in sections) + "</div>"]
    for var, groups in sections:
        parts.append(f"<div class=variant id='v{var['name']}'><nav>" + "".join(
            f"<a href='#v{var['name']}g{i}'>{html.escape(t)}</a>" for i, (t, _, _) in enumerate(groups)) + "</nav>")
        for i, (title, pg, cs) in enumerate(groups):
            parts.append(f"<section id='v{var['name']}g{i}'><h2>{html.escape(title)} <span class=muted>· PDF page {pg}"
                         f" · {len(cs)} chunk(s)</span></h2><div class=row><div><img loading=lazy alt='page {pg}' data-p='{pg}'></div><div>")
            for c in cs:
                flags = []
                if c["tokens"] < cfg["chunk"]["min_tokens_flag"]:
                    flags.append("short")
                if c["tokens"] > var["max"]:
                    flags.append("over max")
                if not c["numbers_verified"]:
                    flags.append("numbers not verified")
                m = c["metadata"]
                extra = ""
                if m.get("table_part"):
                    extra += f" · table part {m['table_part']}/{m['table_parts']}"
                if m.get("figure_part"):
                    extra += f" · figure part {m['figure_part']}/{m['figure_parts']}"
                if m.get("overlap_tokens"):
                    extra += f" · overlap {m['overlap_tokens']} tok"
                parts.append(f"<div class=ch><div class=meta><b>{html.escape(c['chunk_id'])}</b> · {c['source_type']} · "
                             f"{c['tokens']} tok · {html.escape(c['source'])}{extra}"
                             + "".join(f"<span class=flag>{f}</span>" for f in flags) +
                             f"<br>{html.escape(c['citation'])}"
                             + (f" · {html.escape(c['subsection'])}" if c.get("subsection") else "") +
                             f"</div><pre>{html.escape(c['text_en'])}</pre>")
                if m.get("alt_description"):
                    parts.append(f"<details><summary>Qwen3 alt_description</summary><pre>{html.escape(m['alt_description'])}</pre></details>")
                parts.append("</div>")
            parts.append("</div></div></section>")
        parts.append("</div>")
    parts.append("<script>const IM=" + json.dumps({str(k): v for k, v in imgs.items()}) + ";"
                 "document.querySelectorAll('img[data-p]').forEach(i=>i.src=IM[i.dataset.p]);"
                 "const bs=[...document.querySelectorAll('.tabs button')];"
                 "function show(v){document.querySelectorAll('.variant').forEach(d=>d.style.display=d.id==='v'+v?'':'none');"
                 "bs.forEach(b=>b.classList.toggle('on',b.dataset.v===v));}"
                 "bs.forEach(b=>b.onclick=()=>show(b.dataset.v));show(bs[0].dataset.v);</script></body></html>")
    path = os.path.join(out, "chunks_preview.html")
    open(path, "w", encoding="utf-8").write("".join(parts))
    return path
