"""Stage 2 — raw corpus + per-app compile baseline + analyzer profile.

Emits one JSONL row per procedure/trigger member of every mineable .al file in
the selected repos, plus `app_baseline.json` (which apps compile clean and their
analyzer-hit counts) so downstream generators know a valid starting point.
"""
from __future__ import annotations
import json, os, shutil, hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .corpus import records_for_file
from .compile_gate import prepare, compile_app
from .sources import SOURCES, VENDOR

DATA = Path.home() / "bc-al-data" / "data"
CORPUS = DATA / "corpus.jsonl"
BASELINE = DATA / "app_baseline.json"


def _mine_repos() -> list[tuple[str, Path, str]]:
    out = []
    for s in SOURCES:
        if s.role != "mine":
            continue
        root = VENDOR / s.key
        if root.exists():
            out.append((s.url.split("github.com/")[-1], root, s.subdir))
    return out


def _app_dirs(root: Path) -> list[Path]:
    return sorted({p.parent for p in root.rglob("app.json")
                   if "/.alpackages/" not in str(p)})


def _baseline_one(args) -> dict:
    repo, app_dir_str = args
    app_dir = Path(app_dir_str)
    work = Path("/tmp/bcaldata-baseline") / hashlib.sha1(app_dir_str.encode()).hexdigest()[:16]
    if work.exists():
        shutil.rmtree(work)
    try:
        shutil.copytree(app_dir, work)
        v = prepare(work)
        r = compile_app(work, v, analyzers=True)
        return {"repo": repo, "app_dir": str(app_dir), "symbol_version": v,
                "error_clean": r.clean, "n_errors": len(r.errors),
                "error_codes": sorted({c for s, c, _ in r.diagnostics if s == "error"}),
                "n_analyzer_hits": len(r.analyzer_hits),
                "analyzer_rules": sorted({c for _, c in r.analyzer_hits})}
    except Exception as e:  # noqa: BLE001
        return {"repo": repo, "app_dir": str(app_dir), "error_clean": False, "exception": str(e)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def build_baselines(workers: int = max(1, os.cpu_count() // 2)) -> None:
    jobs = [(repo, str(d)) for repo, root, _ in _mine_repos() for d in _app_dirs(root)]
    print(f"compiling {len(jobs)} app baselines on {workers} workers ...")
    done = {}
    if BASELINE.exists():
        done = {r["app_dir"]: r for r in json.loads(BASELINE.read_text())}
    todo = [j for j in jobs if j[1] not in done]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, res in enumerate(ex.map(_baseline_one, todo), 1):
            done[res["app_dir"]] = res
            if i % 10 == 0:
                BASELINE.write_text(json.dumps(list(done.values()), indent=2))
                print(f"  {i}/{len(todo)}  clean so far: {sum(v['error_clean'] for v in done.values())}")
    BASELINE.write_text(json.dumps(list(done.values()), indent=2))
    n_clean = sum(v["error_clean"] for v in done.values())
    print(f"baselines: {n_clean}/{len(done)} apps compile clean")


def _clean_app_dirs() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {r["app_dir"] for r in json.loads(BASELINE.read_text()) if r.get("error_clean")}


def build_members(only_clean_apps: bool = True) -> None:
    clean = _clean_app_dirs()
    n = 0
    with CORPUS.open("w") as fh:
        for repo, root, subdir in _mine_repos():
            for f in sorted((root / subdir).rglob("*.al")):
                if only_clean_apps:
                    app = next((a for a in (str(p.parent) for p in f.parents for _ in [0]
                                            if (p.parent / "app.json").is_file())), None)
                    # simpler: walk up for app.json
                    app = None
                    for anc in f.parents:
                        if (anc / "app.json").is_file():
                            app = str(anc); break
                    if app is not None and app not in clean:
                        continue
                try:
                    for rec in records_for_file(f, repo, root):
                        fh.write(json.dumps(rec) + "\n")
                        n += 1
                except Exception as e:  # noqa: BLE001
                    fh.write(json.dumps({"_parse_error": str(e), "path": str(f)}) + "\n")
    print(f"corpus: {n} member records -> {CORPUS}")
