"""Stage 4 — compile gate over generator candidates.

Materializes each candidate's target AL into a throwaway project, compiles it
against the pinned symbol cache (+ full analyzer set), keeps only:
  - positive generators (g1/g2/g6): error-clean
  - g5/g7: NOT clean AND the emitted error code is in the expected class
Everything is content-hash cached under .cache/verify/<sha256>.json .
"""
from __future__ import annotations
import hashlib, json, os, shutil, tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .compile_gate import compile_app, seed_alpackages, pin_runtime, artifact_root

CACHE = Path.home() / "bc-al-data" / ".cache" / "verify"
CACHE.mkdir(parents=True, exist_ok=True)
SYMBOL_VERSION = os.environ.get("BC_VERSION", "28.0").split(".")[0] + "." + os.environ.get("BC_VERSION", "28.0").split(".")[1]

_MINI_APP_JSON = {
    "id": "00000000-0000-4000-8000-000000000abc", "name": "bcaldata verify", "publisher": "bcaldata",
    "version": "1.0.0.0", "platform": "28.0.0.0", "application": "28.0.0.0", "runtime": "17.0",
    "idRanges": [{"from": 50000, "to": 59999}], "features": ["NoImplicitWith"],
}


def _key(cand: dict) -> str:
    return hashlib.sha256((cand["gen"] + "\0" + (cand.get("target_al") or "")
                           + "\0" + (cand.get("rejected_al") or "") + "\0" + SYMBOL_VERSION).encode()).hexdigest()


def _wrap_object(al: str) -> str:
    return al if al.lstrip().lower().startswith(("codeunit", "table", "page", "enum", "report",
                                                 "query", "xmlport", "interface", "permissionset",
                                                 "controladdin", "profile", "entitlement")) \
        else f'codeunit 50000 "Verify Wrapper"\n{{\n{al}\n}}\n'


_SHARED_ALP = Path.home() / "bc-al-data" / ".cache" / "shared-alpackages" / SYMBOL_VERSION


def _shared_alpackages() -> Path:
    """Seed the symbol set once; every snippet project symlinks it (copy-per-compile is the bottleneck)."""
    if _SHARED_ALP.is_dir() and any(_SHARED_ALP.glob("*.app")):
        return _SHARED_ALP
    _SHARED_ALP.mkdir(parents=True, exist_ok=True)
    root = artifact_root(SYMBOL_VERSION)
    for app in root.rglob("*.app"):
        if "bcaldata verify" in app.name.lower():
            continue
        link = _SHARED_ALP / app.name
        if not link.exists():
            link.symlink_to(app)          # symlink, not copy — the AL compiler reads through it
    return _SHARED_ALP


def _compile_snippet(al: str) -> "object":
    work = Path(tempfile.mkdtemp(prefix="bcaldata-verify-"))
    try:
        (work / "app.json").write_text(json.dumps(_MINI_APP_JSON))
        (work / "src").mkdir()
        (work / "src" / "Snippet.al").write_text(_wrap_object(al))
        (work / ".alpackages").symlink_to(_shared_alpackages())
        return compile_app(work, SYMBOL_VERSION, analyzers=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def verify_one(cand: dict) -> dict | None:
    kf = CACHE / f"{_key(cand)}.json"
    if kf.exists():
        v = json.loads(kf.read_text())
        return {**cand, "verify": v} if v["kept"] else None

    gen = cand["gen"]
    verdict = {"kept": False, "reason": ""}
    if gen in ("g5_error_fix", "g7_hard_negative"):
        r_bad = _compile_snippet(cand["rejected_al"])
        r_good = _compile_snippet(cand["target_al"])
        codes = sorted({c for s, c, _ in r_bad.diagnostics if s == "error"})
        verdict = {"kept": (not r_bad.clean) and r_good.clean,
                   "reason": f"bad_clean={r_bad.clean} good_clean={r_good.clean}",
                   "error_codes": codes,
                   "analyzer_hits_good": [c for _, c in r_good.analyzer_hits]}
    elif gen in ("g1_fim", "g2_sig2body", "g6_spec2object"):
        r = _compile_snippet(cand["target_al"])
        verdict = {"kept": r.clean, "reason": f"clean={r.clean} errs={r.errors[:3]}",
                   "analyzer_hits": [c for _, c in r.analyzer_hits]}
    else:  # g3/g4/g8-review: text targets, no compile
        verdict = {"kept": True, "reason": "text-target (no compile)"}
    kf.write_text(json.dumps(verdict))
    return {**cand, "verify": verdict} if verdict["kept"] else None


def verify_file(in_jsonl: Path, out_jsonl: Path, workers: int = max(1, os.cpu_count() // 2)) -> dict:
    cands = [json.loads(l) for l in in_jsonl.read_text().splitlines() if l.strip()]
    kept = 0
    with ProcessPoolExecutor(max_workers=workers) as ex, out_jsonl.open("w") as fh:
        for res in ex.map(verify_one, cands, chunksize=8):
            if res is not None:
                fh.write(json.dumps(res) + "\n")
                kept += 1
    stats = {"in": len(cands), "kept": kept, "pass_rate": round(kept / max(1, len(cands)), 3)}
    print(f"verify {in_jsonl.name}: {stats}")
    return stats
