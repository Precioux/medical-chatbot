"""Stage 2: build unified_output.jsonl with build_unified.py, using the stage-1 translations.

Inputs: stage1_translate/translations.jsonl + the frozen upstream artifacts in config.inputs.
Outputs (stage2_extract/): unified_output.jsonl, merge_report.json, translated_blocks.json
"""
import collections, os, time

from pipeline.common import (StageFailed, inp, load_config, read_jsonl, script_runs_re, seg_key, stage_dir,
                             vietnamese_line, write_json)

CFG = None


def _lookup(key, table):
    """Translate run `key` (whitespace-free) from the page's segment table. A run in a block can join several
    stage-1 segments (e.g. table cells read as one line): decompose greedily by the longest matching segment;
    digits/punctuation between segments are kept as they are. -> (text, [seg rows]) or None."""
    if key in table:
        return table[key]["content_en"], [table[key]]
    keys = sorted(table, key=len, reverse=True)
    i, parts, used = 0, [], []
    while i < len(key):
        k = next((k for k in keys if key.startswith(k, i)), None)
        if k:
            parts.append(table[k]["content_en"]); used.append(table[k]); i += len(k)
        elif not key[i].isalpha():
            parts.append(key[i]); i += 1
        else:
            return None
    return " ".join(parts), used


def decide(cfg, rows):
    """Which translations go into the blocks: qe_chrf >= extract.mt_min_chrf and no number lost. Others get an
    English placeholder (extract.mt_unreliable: placeholder) that keeps the source's numbers, or the raw MT (keep)."""
    ec = cfg["extract"]
    names = {**{k: v["name"] for k, v in cfg["translate"]["scripts"].items()}, "vie": "Vietnamese"}
    for r in rows:
        r["reliable"] = (r.get("qe_chrf") or 0) >= ec["mt_min_chrf"] and not (r.get("flags") or {}).get("numbers_lost")
        if r["reliable"] or ec["mt_unreliable"] == "keep":
            r["content_en"] = r["translation"]
        else:                                                # never put a hallucinated translation into the index
            ns = r.get("source_numbers") or []
            r["content_en"] = (f"[{names[r['lang']]} text, machine translation withheld (unreliable)"
                               + (f"; numbers in it: {', '.join(ns)}" if ns else "") + "]")
    return rows


def apply_translations(blocks, path):
    cfg = CFG or load_config()
    rows = decide(cfg, read_jsonl(path))
    table = collections.defaultdict(dict)
    for r in rows:
        table[r["page"]][r["key"]] = r
    runs = script_runs_re(cfg)
    stats, unmatched, used_ids = collections.Counter(), [], set()
    for b in blocks:
        text, langs, segs = b["content"], set(), []
        hits = [(m.start(), m.end(), lang) for lang, rx in runs.items() for m in rx.finditer(text)]
        vi = any(vietnamese_line(cfg, line)[0] for line in text.split("\n"))   # Vietnamese: whole lines
        if not hits and not vi:
            continue
        out = text
        for s, e, lang in sorted(hits, reverse=True):  # right to left keeps offsets valid
            res = _lookup(seg_key(out[s:e]), table[b["page"]])
            if res is None:
                unmatched.append({"page": b["page"], "type": b["type"], "run": out[s:e][:120]})
                continue
            out = out[:s] + res[0] + out[e:]
            langs.add(lang); segs += res[1]
        if vi:
            lines = []
            for line in out.split("\n"):
                if vietnamese_line(cfg, line)[0]:
                    res = _lookup(seg_key(line), table[b["page"]])
                    if res is None:
                        unmatched.append({"page": b["page"], "type": b["type"], "run": line[:120]})
                    else:
                        line = res[0]; langs.add("vie"); segs += res[1]
                lines.append(line)
            out = "\n".join(lines)
        if not segs:
            continue
        b["metadata"]["original_text"] = b["content"]
        b["metadata"]["original_language"] = ",".join(sorted(langs))
        b["metadata"]["source_before_translation"] = b["source"]
        b["metadata"]["translated_segments"] = sorted({s["seg_id"] for s in segs})
        flags = sorted({f for s in segs for f in s.get("flags") or {}} | ({"withheld_unreliable"} if any(
            not s["reliable"] for s in segs) else set()))
        b["metadata"]["machine_translation"] = [{"seg": s["seg_id"], "original": s["original"], "nllb": s["translation"],
                                                 "back_translation": s["back_translation"], "qe_chrf": s["qe_chrf"],
                                                 "used": s["reliable"]} for s in segs]
        if flags:
            b["metadata"]["translation_flags"] = flags
        b["content"], b["source"] = out, "nllb-1.3b"
        used_ids |= {s["seg_id"] for s in segs}
        stats["translated_blocks"] += 1
    if unmatched:
        raise StageFailed(f"{len(unmatched)} non-English runs in the blocks have no stage-1 translation: {unmatched[:10]}")
    stats["translation_segments_used"] = len(used_ids)
    stats["translation_segments_unused"] = len(rows) - len(used_ids)
    return stats


def run(cfg, log):
    global CFG
    CFG = cfg
    import build_unified as BU
    import merge_sources as M
    # point both modules at the configured inputs
    BU.PDF, BU.OLD = inp(cfg, "pdf"), inp(cfg, "mmore_build")
    M.DOCLING, M.MMORE, M.CHANDRA = inp(cfg, "docling_json"), inp(cfg, "mmore_json"), inp(cfg, "chandra_pages")
    M.IMAGES, M.SKIPPED = inp(cfg, "image_descriptions"), inp(cfg, "image_descriptions_skipped")
    tr = os.path.join(stage_dir(cfg, "translate"), "translations.jsonl")
    out = stage_dir(cfg, "extract")
    t0 = time.time()
    BU.main(out=os.path.join(out, "unified_output.jsonl"), report_path=os.path.join(out, "merge_report.json"),
            translations=tr)
    blocks = read_jsonl(os.path.join(out, "unified_output.jsonl"))
    tb = [{"id": b["id"], "page": b["page"], "type": b["type"], "language": b["metadata"]["original_language"],
           "source_before": b["metadata"]["source_before_translation"],
           "segments": b["metadata"]["translated_segments"], "flags": b["metadata"].get("translation_flags", []),
           "original": b["metadata"]["original_text"][:300], "english": b["content"][:300]}
          for b in blocks if b["source"] == "nllb-1.3b"]
    used = {s for b in tb for s in b["segments"]}
    segs = decide(cfg, read_jsonl(tr))
    unused = [r for r in segs if r["seg_id"] not in used]
    seg_rows = [{k: r[k] for k in ("seg_id", "page", "original", "translation", "back_translation", "qe_chrf",
                                   "reliable", "content_en")} for r in segs]
    write_json(os.path.join(out, "translated_blocks.json"),
               {"mt_min_chrf": cfg["extract"]["mt_min_chrf"], "mt_unreliable": cfg["extract"]["mt_unreliable"],
                "segments_used": sum(r["reliable"] for r in segs), "segments_withheld": sum(not r["reliable"] for r in segs),
                "blocks": tb, "segments": seg_rows, "unused_segments": unused})
    left = [b["id"] for b in blocks if any(rx.search(b["content"]) for rx in script_runs_re(cfg).values())]
    if left:
        raise StageFailed(f"non-English text left in blocks {left}")
    log(f"{len(blocks)} blocks; {len(tb)} translated: {[(b['id'], b['page'], b['type']) for b in tb]}")
    if unused:
        log(f"WARNING: {len(unused)} stage-1 segments matched no block: {[(u['seg_id'], u['page']) for u in unused]}")
    return {"blocks": len(blocks), "translated_blocks": tb, "unused_segments": len(unused),
            "seconds": round(time.time() - t0, 1)}
