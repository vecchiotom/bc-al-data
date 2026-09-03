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


# --- resident-server fast path -----------------------------------------
# For the positive generators (g1/g2/g6) an error-clean check is the whole
# verdict. The agentic AL LSP has no diagnostics channel (see alsp.py), so the
# fast path keeps one resident AL MCP server per worker and calls its warm
# `al_compile` (~2-4x faster than a cold `al compile` — no process start, JIT,
# or 350-package symbol load per candidate). g5/g7 still need a real `/out`
# artifact and the exact error class, so they stay on `_compile_snippet`.

_LSP_GENS = {"g1_fim", "g2_sig2body", "g6_spec2object"}
_WORKER_MCP: dict[int, object] = {}


def _worker_mcp() -> "object":
    """One ALLanguageServer (LSP nav + co-resident MCP compiler) per process,
    over a throwaway project that symlinks the shared symbol set."""
    import os as _os

    from .alsp import ALLanguageServer

    key = _os.getpid()
    srv = _WORKER_MCP.get(key)
    if srv is not None:
        return srv
    work = Path(tempfile.mkdtemp(prefix="bcaldata-lsp-"))
    (work / "app.json").write_text(json.dumps(_MINI_APP_JSON))
    (work / "src").mkdir()
    (work / ".alpackages").symlink_to(_shared_alpackages())
    srv = ALLanguageServer(work, timeout=240).start()
    _WORKER_MCP[key] = srv
    return srv


def _verify_one_lsp(cand: dict) -> dict | None:
    """Resident-server verdict for a positive-generator candidate; compile
    fallback for other generators and on any error."""
    kf = CACHE / f"{_key(cand)}.json"
    if kf.exists():
        v = json.loads(kf.read_text())
        return {**cand, "verify": v} if v["kept"] else None
    if cand["gen"] not in _LSP_GENS:
        return verify_one(cand)
    try:
        srv = _worker_mcp()
        snippet = _wrap_object(cand["target_al"])
        f = Path(srv.project_dir) / "src" / "Snippet.al"
        diags = srv.diagnostics(f, snippet)
        err = sorted({d["code"] for d in diags if d["severity"] == 1 and d["code"]})
        hits = sorted({d["code"] for d in diags if d["severity"] == 2 and d["code"]})
        verdict = {"kept": not err, "reason": f"resident clean={not err} errs={err[:3]}",
                   "analyzer_hits": hits, "via": "lsp"}
    except Exception as e:  # noqa: BLE001 - fall back to the authoritative compile
        return verify_one({**cand, "_lsp_error": str(e)})
    kf.write_text(json.dumps(verdict))
    return {**cand, "verify": verdict} if verdict["kept"] else None


def verify_batch_via_lsp(candidates: list[dict], workers: int | None = None) -> list[dict]:
    """Verify `candidates` reusing one resident AL server per worker. Returns
    kept rows. Non-fast-path generators still route through `verify_one`."""
    workers = workers or max(1, (os.cpu_count() or 2) // 2)
    kept: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_verify_one_lsp, candidates, chunksize=4):
            if res is not None:
                kept.append(res)
    return kept


def _verify_file_inapp(cands: list[dict], in_jsonl: Path, out_jsonl: Path, workers: int) -> dict:
    """In-app verify. g5/g7 candidates are grouped by origin app so each app's
    worktree is copied + symbol-seeded once and reused across its mutations;
    g1/g2/g6/text targets go one-by-one (mostly the instant baseline fast path)."""
    from .verify_inapp import _resolve_origin, verify_g5_group, verify_one_inapp

    batched, singles = {}, []
    for c in cands:
        if c["gen"] in ("g5_error_fix", "g7_hard_negative"):
            origin = _resolve_origin(c)
            if origin is not None:
                app_dir, _, _, version = origin
                batched.setdefault((str(app_dir), version), []).append(c)
                continue
        singles.append(c)

    kept: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        group_futs = [ex.submit(verify_g5_group, app, ver, group)
                      for (app, ver), group in batched.items()]
        for res in ex.map(verify_one_inapp, singles, chunksize=8):
            if res is not None:
                kept.append(res)
        for f in group_futs:
            kept.extend(f.result())

    with out_jsonl.open("w") as fh:
        for r in kept:
            fh.write(json.dumps(r) + "\n")
    stats = {"in": len(cands), "kept": len(kept),
             "pass_rate": round(len(kept) / max(1, len(cands)), 3), "mode": "inapp",
             "batched_apps": len(batched)}
    print(f"verify {in_jsonl.name}: {stats}")
    return stats


def verify_file(in_jsonl: Path, out_jsonl: Path, workers: int = max(1, os.cpu_count() // 2),
                mode: str = "compile") -> dict:
    """Compile-gate `in_jsonl` into `out_jsonl`.

    mode="compile" (default): every candidate through a cold `al compile`.
    mode="lsp": g1/g2/g6 through a resident AL server (warm `al_compile`,
    error-clean check); g5/g7 and text targets stay on the cold `al compile`.
    """
    cands = [json.loads(l) for l in in_jsonl.read_text().splitlines() if l.strip()]
    if mode == "inapp":
        return _verify_file_inapp(cands, in_jsonl, out_jsonl, workers)
    if mode == "lsp":
        runner = _verify_one_lsp
    else:
        runner = verify_one
    kept = 0
    with ProcessPoolExecutor(max_workers=workers) as ex, out_jsonl.open("w") as fh:
        for res in ex.map(runner, cands, chunksize=8):
            if res is not None:
                fh.write(json.dumps(res) + "\n")
                kept += 1
    stats = {"in": len(cands), "kept": kept, "pass_rate": round(kept / max(1, len(cands)), 3),
             "mode": mode}
    print(f"verify {in_jsonl.name}: {stats}")
    return stats
