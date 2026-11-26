"""pipeline_report.md: rewritten at the end of every run_pipeline.py call from the stage folders' own outputs."""
import collections, json, os

from pipeline.common import STAGES, STAGE_DIRS, p


def _load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def _cut(s, n=90):
    s = " ".join(str(s).split())
    return (s[:n] + "…") if len(s) > n else s


def _md(s):
    return str(s).replace("|", "\\|")


def write_report(cfg):
    root = p(cfg["output_root"])
    d = {s: os.path.join(root, STAGE_DIRS[s]) for s in STAGES}
    L = ["# Pipeline report", ""]

    # ---- stages
    L += ["## Stages", "", "| # | stage | folder | status | finished | host | time (s) |", "|---|---|---|---|---|---|---|"]
    for i, s in enumerate(STAGES, 1):
        done, fail = _load(os.path.join(d[s], "_done.json")), _load(os.path.join(d[s], "_failed.json"))
        if done:
            L.append(f"| {i} | {s} | {STAGE_DIRS[s]}/ | done | {done['finished']} | {done.get('host', '')} | {done['seconds']} |")
        elif fail:
            L.append(f"| {i} | {s} | {STAGE_DIRS[s]}/ | **FAILED**: {_md(_cut(fail['error'], 120))} | {fail['finished']} | | |")
        else:
            L.append(f"| {i} | {s} | {STAGE_DIRS[s]}/ | not run | | | |")
    L.append("")

    # ---- translation
    tr = _load(os.path.join(d["translate"], "report.json"))
    tb = _load(os.path.join(d["extract"], "translated_blocks.json"))
    L += ["## Stage 1: translation", ""]
    if tr:
        L += [f"Model {tr['model']}. Non-English text was found on PDF pages **{', '.join(map(str, tr['pages_translated']))}** "
              f"({tr['segments_total']} unique segments). Segments per page: "
              + "; ".join(f"p{k}: {', '.join(f'{n} {t}' for t, n in v.items())}" for k, v in tr["segments_per_page"].items()) + ".", ""]
        if tr.get("stats"):
            L.append(f"Translation counters: {tr['stats']}.")
        L.append(f"Segments that lost a number in translation: {tr['segments_with_numbers_lost'] or 'none'}. "
                 f"Segments whose source text is itself repetitive (Chandra loops): {len(tr['segments_with_repetitive_source'])}. "
                 f"Vietnamese-looking lines rejected (fewer than {cfg['translate']['vietnamese']['min_words_per_line']} "
                 f"Vietnamese words): {len(tr['vietnamese_candidates_rejected'])}.")
        L.append("")
    if tb:
        L += ["Translated blocks (content replaced by the English text; original in `metadata.original_text`):", "",
              "| block | page | type | lang | was | flags | original | English |", "|---|---|---|---|---|---|---|---|"]
        for b in tb["blocks"]:
            L.append(f"| {b['id']} | {b['page']} | {b['type']} | {b['language']} | {b['source_before']} | "
                     f"{', '.join(b['flags']) or ''} | {_md(_cut(b['original'], 60))} | {_md(_cut(b['english'], 90))} |")
        L.append("")
        if tb.get("unused_segments"):
            L.append(f"Stage-1 segments that matched no block: {[(u['seg_id'], u['page']) for u in tb['unused_segments']]}")
            L.append("")
    if tb and tb.get("segments"):
        L += [f"Quality gate (stage 2): a translation is used only if the chrF of its back-translation against the source "
              f"is >= {tb['mt_min_chrf']} and no number was lost; otherwise `{tb['mt_unreliable']}`. "
              f"Used: {tb['segments_used']}, withheld: {tb['segments_withheld']}.", "",
              "| seg | page | original | NLLB output | back-translation | chrF | used |", "|---|---|---|---|---|---|---|"]
        for r in tb["segments"]:
            L.append(f"| {r['seg_id']} | {r['page']} | {_md(_cut(r['original'], 40))} | {_md(_cut(r['translation'], 70))} | "
                     f"{_md(_cut(r['back_translation'], 30))} | {r['qe_chrf']} | {'yes' if r['reliable'] else 'no'} |")
        L.append("")

    # ---- verify
    vd = _load(os.path.join(d["verify"], "_done.json")) or _load(os.path.join(d["verify"], "_failed.json"))
    L += ["## Stage 3: completeness check", ""]
    if vd and vd.get("summary"):
        s = vd["summary"]
        L += [f"Numbers by value **{s['numbers']}**, symbols **{s['symbols']}** (expected "
              f"{cfg['verify']['expected_numbers']}/{cfg['verify']['expected_numbers']} and "
              f"{cfg['verify']['expected_symbols']}/{cfg['verify']['expected_symbols']}). Word coverage {s['word_coverage']:.2%}, "
              f"exact number form {s['number_coverage_exact']:.2%}. Figures {s['figures']}, unaccounted {s['figures_unaccounted']}. "
              f"{s['pages_checked']} pages checked; image-only pages not checked: {len(s['pages_image_only_not_checked'])}.", ""]
    elif vd:
        L += [f"FAILED: {vd.get('error')}", ""]

    # ---- sections
    sec = _load(os.path.join(d["chunk"], "sections.json"))
    L += ["## Sections (from the PDF's table of contents)", ""]
    if sec:
        L += [f"The printed TOC (PDF pages {sec['toc_pages']}) lists **{sec['sections_in_toc']} numbered sections** in "
              f"{len(sec['chapters'])} chapters: " + ", ".join(f"Chapter {c['chapter']} {c['title']} (from PDF p{c['pdf_page']}): "
                                                               f"{sec['sections_per_chapter'].get(c['chapter'], 0)} sections"
                                                               for c in sec["chapters"]) + ". "
              f"The work plan's figure of 28 sections does not match the TOC.", "",
              f"- Every section's title line was looked up in the text layer at TOC page + {cfg['chunk']['page_offset']}: "
              f"not found: {sec['sections_heading_not_found'] or 'none'}; found on a different page: "
              f"{sec['sections_start_not_at_expected_page'] or 'none'}.",
              f"- Sections 45 and 46 have the same title in the TOC and in the body (\"Infectious Endocarditis\", PDF p"
              f"{next(s['start_page'] for s in sec['sections'] if s['number'] == 45)} and p"
              f"{next(s['start_page'] for s in sec['sections'] if s['number'] == 46)}); they stay two sections.",
              f"- Title spelling taken from the body heading where the TOC has a typo: "
              + "; ".join(f"§{n}: " + ", ".join(f"{a} → {b}" for a, b in f) for n, f in sec["title_fixes"].items()) + ".",
              f"- Sections without a detectable reference-list heading: {sec['sections_without_reference_heading'] or 'none'}.",
              "",
              f"**How the stage-2 section labels map onto the TOC.** Stage 2 labels blocks with {sec['stage2_labels']} values: "
              f"51 numbered sections plus {', '.join(x.lstrip('- ') for x in sec['stage2_labels_not_in_toc'])}. Each numbered label maps to the TOC "
              f"section with the same number; labels where any block lands in a different TOC section: "
              f"{[m['stage2_label'] for m in sec['stage2_labels_disagreeing']] or 'none'}. "
              f"The unnumbered labels map to front matter (excluded) and the chapter title pages (excluded).",
              "",
              f"Docling found {sec['docling_section_headers']} section headers (all levels). "
              f"{len(sec['docling_headers_matching_a_toc_title'])} of them resemble a TOC title "
              f"({sum(1 for m in sec['docling_headers_matching_a_toc_title'] if m['on_start_page'])} on the section's start page; "
              f"the rest are sub-headings such as \"Pulmonary embolism (19.6%)\" inside other sections). "
              f"TOC sections with no Docling header at all: {sec['toc_sections_without_docling_header']}. "
              f"Docling headers are not used for sectioning.", "",
              "<details><summary>Section table</summary>", "",
              "| § | ch | title | TOC page | PDF start | heading line in text layer |", "|---|---|---|---|---|---|"]
        for s in sec["sections"]:
            L.append(f"| {s['number']} | {s['chapter']} | {_md(s['title'])} | {s['printed_page']} | {s['start_page']} | "
                     f"{_md(_cut(s['heading_line'] or '-', 70))} |")
        L += ["", "</details>", ""]

    # ---- chunks
    st = _load(os.path.join(d["chunk"], "chunk_stats.json"))
    val = _load(os.path.join(d["validate"], "validation.json"))
    L += ["## Stage 4: chunks", ""]
    if st:
        L += [f"Excluded from the index (`excluded.jsonl`, {st['excluded_records']} records): {st['excluded']}.", "",
              "| variant | chunks | body_text | table | flowchart | figure | tokens min / median / max | over max | text chunks with overlap | mean overlap |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for v in cfg["chunk"]["variants"]:
            x = st[v["name"]]
            pt, t = x["per_source_type"], x["tokens"]
            L.append(f"| {v['name']} (max {v['max']}) | {x['chunks']} | {pt.get('body_text', 0)} | {pt.get('table', 0)} | "
                     f"{pt.get('flowchart', 0)} | {pt.get('figure', 0)} | {t['min']} / {t['median']} / {t['max']} | "
                     f"{x['over_max']} {x['over_max_by_type']} | {x['text_chunks_with_overlap']} | {x['mean_overlap_fraction']:.0%} |")
        L.append("")
        L += ["Tokens per source_type (min / median / max):", "", "| variant | " + " | ".join(["body_text", "table", "flowchart", "figure"]) + " |",
              "|---|---|---|---|---|"]
        for v in cfg["chunk"]["variants"]:
            tp = st[v["name"]]["tokens_per_type"]
            L.append(f"| {v['name']} | " + " | ".join(f"{tp[k]['min']} / {tp[k]['median']} / {tp[k]['max']}" if k in tp else "-"
                                                      for k in ["body_text", "table", "flowchart", "figure"]) + " |")
        x = st[cfg["chunk"]["variants"][0]["name"]]
        c = x["counters"]
        L += ["", f"Flowcharts: {c.get('flowcharts_paired_with_qwen3', 0)} Chandra algorithm blocks were matched to the Qwen3 "
              f"description of the same figure (Chandra text kept, Qwen3 in `metadata.alt_description`); the other "
              f"Qwen3 descriptions are figure chunks with `numbers_verified: false`. Sentences joined across a line "
              f"break: {c.get('sentences_joined_across_lines', 0)}, across a block/page break: "
              f"{c.get('sentences_joined_across_blocks', 0)}. Sentences longer than max that had to be cut: "
              f"{c.get('forced_split_sentences', 0)}.", ""]
        L += ["Over-max chunks are flowcharts kept whole (rule 4 outranks the size limit) and single table rows longer "
              "than the limit (a row is never split).", ""]

    # ---- validation
    L += ["## Stage 5: validation", ""]
    if val:
        L += ["| check | " + " | ".join(v["name"] for v in cfg["chunk"]["variants"]) + " |", "|---|" + "---|" * len(cfg["chunk"]["variants"])]
        rows = collections.OrderedDict()
        for v in cfg["chunk"]["variants"]:
            r = val.get(v["name"])
            if not r:
                continue
            ns = r["numbers_symbols"]
            a, b = ns["chunks_plus_excluded_all_pages"], next(x for k, x in ns.items() if k.startswith("index_only"))
            rows.setdefault("1 numbers (chunks + excluded, all pages)", []).append(f"{a['numbers']} {'✓' if ns['pass'] else '✗'}")
            rows.setdefault("1 symbols (chunks + excluded, all pages)", []).append(a["symbols"])
            rows.setdefault("1 numbers / symbols, index only (p17+, reference lists removed from the reference)", []).append(
                f"{b['numbers']} / {b['symbols']}")
            o = r["orphans"]
            rows.setdefault("2 orphan blocks / lost sentences", []).append(
                f"{len(o['blocks_not_in_chunks_or_excluded'])} / {o['sentences_not_found_count']} {'✓' if o['pass'] else '✗'}")
            sc = r["sections"]
            rows.setdefault("3 chunks crossing a section / table parts without header", []).append(
                f"{len(sc['chunks_crossing_a_section'])} / {len(sc['table_parts_without_header'])} {'✓' if sc['pass'] else '✗'}")
            rows.setdefault("4 citations not matching", []).append(f"{len(r['citations']['bad'])} {'✓' if r['citations']['pass'] else '✗'}")
            tk = r["tokens"]
            rows.setdefault(f"5 chunks under {cfg['chunk']['min_tokens_flag']} tokens", []).append(
                f"{tk['under_min_count']} {tk['under_min_by_type']}")
            rows.setdefault("5 numbers_verified (type:value)", []).append(str(tk["numbers_verified"]))
        for k, v in rows.items():
            L.append(f"| {k} | " + " | ".join(_md(x) for x in v) + " |")
        L.append("")
        L += [f"Overall: {'**all checks passed**' if not val.get('failures') else '**FAILED**: ' + '; '.join(val['failures'])}.", ""]
        for v in cfg["chunk"]["variants"]:
            r = val.get(v["name"])
            if not r:
                continue
            L += [f"Token histogram, variant {v['name']}:", "", "| type | " + " | ".join(next(iter(r["tokens"]["histogram"].values())).keys()) + " |",
                  "|---|" + "---|" * len(next(iter(r["tokens"]["histogram"].values())))]
            for t, h in r["tokens"]["histogram"].items():
                L.append(f"| {t} | " + " | ".join(str(x) for x in h.values()) + " |")
            L.append("")
            if r["tokens"]["under_min"]:
                L += [f"<details><summary>Chunks under {cfg['chunk']['min_tokens_flag']} tokens ({v['name']})</summary>", ""]
                L += [f"- {c} ({t}, {n} tok): {_md(_cut(x, 70))}" for c, t, n, x in r["tokens"]["under_min"]]
                L += ["", "</details>", ""]
        L += [f"Preview: `{os.path.relpath(os.path.join(d['validate'], 'chunks_preview.html'), p('.'))}`", ""]
    path = os.path.join(root, "pipeline_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return path
