"""Stage 3: completeness check of stage2_extract/unified_output.jsonl against the PDF text layer (verify_output.py).

Gate: numbers found by value == expected_numbers (6,362) and symbols == expected_symbols (245), no missing ones.
On success the checked file is copied to stage3_verify/unified_output.verified.jsonl: stage 4 reads only that.
Outputs: completeness_report.json, review.html, unified_output.verified.jsonl
"""
import os, shutil, time

from pipeline.common import StageFailed, inp, stage_dir


def run(cfg, log):
    import verify_output as V
    V.PDF, V.DOCLING = inp(cfg, "pdf"), inp(cfg, "docling_json")
    V.DESC, V.SKIP = inp(cfg, "image_descriptions"), inp(cfg, "image_descriptions_skipped")
    V.PAGES = inp(cfg, "page_images")
    src = os.path.join(stage_dir(cfg, "extract"), "unified_output.jsonl")
    out = stage_dir(cfg, "verify")
    t0 = time.time()
    s = V.main(unified=src, report=os.path.join(out, "completeness_report.json"),
               review_path=os.path.join(out, "review.html"))
    exp_n, exp_s = cfg["verify"]["expected_numbers"], cfg["verify"]["expected_symbols"]
    found_n, found_s = s["numbers_ref"] - s["numbers_missing"], s["symbols_ref"] - s["symbols_missing"]
    res = {"numbers": f"{found_n}/{s['numbers_ref']}", "symbols": f"{found_s}/{s['symbols_ref']}",
           "word_coverage": s["word_coverage"], "number_coverage_exact": s["number_coverage_exact"],
           "figures": s["figures"], "figures_unaccounted": len(s["figures_unaccounted"]),
           "leftovers": s["leftovers"], "pages_checked": s["pages_checked"],
           "pages_image_only_not_checked": s["pages_image_only_not_checked"], "seconds": round(time.time() - t0, 1)}
    log(f"numbers {res['numbers']} (expected {exp_n}), symbols {res['symbols']} (expected {exp_s}), "
        f"words {s['word_coverage']:.2%}")
    if not (s["numbers_ref"] == found_n == exp_n and s["symbols_ref"] == found_s == exp_s):
        raise StageFailed(f"completeness check failed: numbers {res['numbers']} (expected {exp_n}/{exp_n}), "
                          f"symbols {res['symbols']} (expected {exp_s}/{exp_s}); pages with missing numbers "
                          f"{s['pages_flagged_missing_numbers']}, symbols {s['pages_with_missing_symbols']}")
    shutil.copyfile(src, os.path.join(out, "unified_output.verified.jsonl"))
    return res
