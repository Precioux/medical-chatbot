"""Shared helpers: config, paths, jsonl, script detection."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

STAGES = ["translate", "extract", "verify", "chunk", "validate"]
STAGE_DIRS = {"translate": "stage1_translate", "extract": "stage2_extract", "verify": "stage3_verify",
              "chunk": "stage4_chunk", "validate": "stage5_validate"}


class StageFailed(RuntimeError):
    """A stage's own check failed: the pipeline stops."""


def load_config(path=None):
    import yaml
    cfg = yaml.safe_load(open(path or os.path.join(ROOT, "config.yaml")))
    os.environ.setdefault("HF_HOME", p(cfg["hf_home"]))
    os.environ.setdefault("USE_TF", "0")                 # senv quirk: transformers must not import TF
    os.environ.setdefault("HF_HUB_OFFLINE", "1")         # models are in the shared cache
    return cfg


def p(rel):
    """Project-relative path -> absolute."""
    return rel if os.path.isabs(rel) else os.path.normpath(os.path.join(ROOT, rel))


def stage_dir(cfg, stage):
    d = os.path.join(p(cfg["output_root"]), STAGE_DIRS[stage])
    os.makedirs(d, exist_ok=True)
    return d


def inp(cfg, key):
    return p(cfg["inputs"][key])


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def write_jsonl(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def write_json(path, obj):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, path)


# ---------------------------------------------------------------- non-English script detection
DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩໐໑໒໓໔໕໖໗໘໙", "01234567890123456789")
VI_TONES = "".join(chr(c) for c in range(0x1EA0, 0x1EFA))


def script_runs_re(cfg):
    """{lang: compiled regex} matching maximal runs of that script. A run starts and ends with a letter of the
    script; spaces, digits and punctuation between such letters belong to the run (Latin letters and line breaks
    end it)."""
    out = {}
    for lang, s in cfg["translate"]["scripts"].items():
        cls = "".join(f"\\u{a:04x}-\\u{b:04x}" for a, b in s["ranges"])
        out[lang] = re.compile(f"[{cls}](?:[{cls} \\t\\u00a0\\u200b\\d.,:;()\\[\\]\\-–—/|\"'!?%«»]*[{cls}])?")
    return out


def vietnamese_line(cfg, line):
    """True if the line has >= min_words_per_line words with Vietnamese-only letters."""
    chars = cfg["translate"]["vietnamese"]["chars"] + VI_TONES
    n = sum(1 for w in line.split() if any(c in chars for c in w))
    return n >= cfg["translate"]["vietnamese"]["min_words_per_line"], n


def seg_key(s):
    return re.sub(r"[\s\u200b]+", "", s)
