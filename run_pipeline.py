#!/usr/bin/env python
"""Part 1 pipeline: scanned guideline PDF -> verified English chunks for the RAG index.

    python run_pipeline.py                         # all stages, skipping the ones already done
    python run_pipeline.py --from chunk            # stages chunk..validate
    python run_pipeline.py --to translate --force  # redo stage 1 only
    python run_pipeline.py --report                # only rewrite pipeline_report.md

Stages (folders under config.output_root, default out/pipeline/):
  1 translate  stage1_translate/  Khmer/Lao/Vietnamese text -> English (NLLB-1.3B, GPU: run on runai)
  2 extract    stage2_extract/    unified_output.jsonl (build_unified.py, with the stage-1 translations)
  3 verify     stage3_verify/     completeness check against the PDF text layer; stops if numbers/symbols != expected
  4 chunk      stage4_chunk/      chunks_256.jsonl, chunks_512.jsonl, excluded.jsonl, sections.json
  5 validate   stage5_validate/   checks on the chunks + chunks_preview.html
A stage is skipped when its _done.json fingerprint (its inputs, its code and its config section) is unchanged;
--force reruns the selected stages anyway. Python: ../miniconda3/envs/senv/bin/python (pymupdf, transformers).
"""
import argparse, datetime, hashlib, importlib, json, os, sys, time, traceback

from pipeline.common import ROOT, STAGES, STAGE_DIRS, StageFailed, inp, load_config, p, stage_dir, write_json

# what each stage depends on: files (project-relative or callables of cfg) and config sections
DEPS = {
    "translate": {"code": ["pipeline/translate.py", "pipeline/common.py", "mt_safety_test.py", "build_unified.py"],
                  "inputs": ["pdf", "chandra_pages", "mmore_build"], "prev": [], "cfg": ["translate"]},
    "extract": {"code": ["pipeline/extract.py", "build_unified.py", "merge_sources.py"],
                "inputs": ["pdf", "docling_json", "mmore_json", "chandra_pages", "image_descriptions", "mmore_build"],
                "prev": [("translate", "translations.jsonl")], "cfg": ["translate", "extract"]},
    "verify": {"code": ["pipeline/verify.py", "verify_output.py"],
               "inputs": ["pdf", "docling_json", "image_descriptions", "image_descriptions_skipped"],
               "prev": [("extract", "unified_output.jsonl")], "cfg": ["verify"]},
    "chunk": {"code": ["pipeline/chunk.py"], "inputs": ["pdf"],
              "prev": [("verify", "unified_output.verified.jsonl")], "cfg": ["chunk"]},
    "validate": {"code": ["pipeline/validate.py", "verify_output.py"], "inputs": ["pdf"],
                 "prev": [("chunk", "chunks_256.jsonl"), ("chunk", "chunks_512.jsonl"), ("chunk", "excluded.jsonl"),
                          ("chunk", "sections.json")], "cfg": ["validate", "verify", "chunk"]},
}


def sha(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def fingerprint(cfg, stage):
    d = DEPS[stage]
    fp = {"code": {c: sha(p(c)) for c in d["code"]},
          "inputs": {k: sha(inp(cfg, k)) for k in d["inputs"]},
          "prev": {}, "cfg": {k: cfg.get(k) for k in d["cfg"]}}
    for st, f in d["prev"]:
        path = os.path.join(stage_dir(cfg, st), f)
        fp["prev"][f"{st}/{f}"] = sha(path) if os.path.exists(path) else None
    return hashlib.sha1(json.dumps(fp, sort_keys=True).encode()).hexdigest()[:16], fp


def done_info(cfg, stage):
    f = os.path.join(stage_dir(cfg, stage), "_done.json")
    return json.load(open(f)) if os.path.exists(f) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", choices=STAGES, default=STAGES[0])
    ap.add_argument("--to", dest="end", choices=STAGES, default=STAGES[-1])
    ap.add_argument("--force", action="store_true", help="rerun the selected stages even if done")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.yaml"))
    ap.add_argument("--report", action="store_true", help="only rewrite pipeline_report.md")
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.report:
        from pipeline.report import write_report
        print("wrote", write_report(cfg))
        return
    sel = STAGES[STAGES.index(a.start):STAGES.index(a.end) + 1]
    run_log = os.path.join(p(cfg["output_root"]), "pipeline.log")
    os.makedirs(os.path.dirname(run_log), exist_ok=True)

    def log(stage):
        def f(msg):
            line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} [{stage}] {msg}"
            print(line, flush=True)
            open(run_log, "a").write(line + "\n")
        return f

    log("pipeline")(f"run {sel} force={a.force} cwd={ROOT}")
    status = 0
    for stage in sel:
        L = log(stage)
        fp, parts = fingerprint(cfg, stage)
        missing = [k for k, v in parts["prev"].items() if v is None]
        if missing:
            L(f"FAILED: missing input from the previous stage: {missing}. Run that stage first.")
            status = 1
            break
        info = done_info(cfg, stage)
        if info and info.get("fingerprint") == fp and not a.force:
            L(f"skip: already done {info['finished']} ({info['seconds']} s)")
            continue
        if info and info.get("fingerprint") != fp:
            L("inputs, code or config changed since the last run: rerunning")
        done = os.path.join(stage_dir(cfg, stage), "_done.json")
        if os.path.exists(done):
            os.remove(done)                              # a failed rerun must not look done
        t0 = time.time()
        try:
            summary = importlib.import_module(f"pipeline.{stage}").run(cfg, L)
        except StageFailed as e:
            L(f"FAILED: {e}")
            write_json(os.path.join(stage_dir(cfg, stage), "_failed.json"),
                       {"error": str(e), "finished": f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}"})
            status = 2
            break
        except Exception:
            L("CRASHED:\n" + traceback.format_exc())
            status = 3
            break
        secs = round(time.time() - t0, 1)
        fail = os.path.join(stage_dir(cfg, stage), "_failed.json")
        if os.path.exists(fail):
            os.remove(fail)
        write_json(done, {"stage": stage, "folder": STAGE_DIRS[stage], "fingerprint": fp, "inputs": parts,
                          "seconds": secs, "finished": f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
                          "host": os.uname().nodename, "summary": summary})
        L(f"done in {secs} s")
    from pipeline.report import write_report
    log("pipeline")(f"report: {write_report(cfg)}")
    sys.exit(status)


if __name__ == "__main__":
    main()
