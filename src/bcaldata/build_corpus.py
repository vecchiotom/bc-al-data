"""Stage 2 — raw corpus + per-app compile baseline + analyzer profile.

Emits one JSONL row per procedure/trigger member of every mineable .al file in
the selected repos, plus `app_baseline.json` (which apps compile clean and their
analyzer-hit counts) so downstream generators know a valid starting point.
"""
from __future__ import annotations
import json, os, re, shutil, hashlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .corpus import records_for_file
from .compile_gate import prepare, compile_app
from .sources import SOURCES, VENDOR

DATA = Path.home() / "bc-al-data" / "data"
CORPUS = DATA / "corpus.jsonl"
BASELINE = DATA / "app_baseline.json"


# `al compile` prints one diagnostic per line: `path/File.al(LINE,COL): warning LC0001: msg`.
_DIAG_LINE = re.compile(
    r"^(?P<path>.+\.al)\((?P<line>\d+),(?P<col>\d+)\):\s*"
    r"(?P<sev>error|warning|info)\s+(?P<code>[A-Z]{2}\d{3,4}i?):\s*(?P<msg>.*)$",
    re.M)


def parse_diagnostics(stdout: str, *, work_dir: Path | None = None,
                      real_dir: Path | None = None) -> dict[str, list]:
    """Re-parse raw `al compile` output into `{abs .al path: [(code, severity, line), ...]}`.

    When the diagnostic paths point inside a throwaway `work_dir` copy, they are
    rewritten onto `real_dir` (the on-disk source app) so the keys match what the
    corpus builder passes to `records_for_file`."""
    out: dict[str, list] = {}
    for m in _DIAG_LINE.finditer(stdout):
        raw = Path(m.group("path"))
        key = raw
        if work_dir is not None and real_dir is not None:
            try:
                key = real_dir / raw.resolve().relative_to(work_dir.resolve())
            except (ValueError, OSError):
                key = real_dir / raw.name if not raw.is_absolute() else raw
        try:
            key = key.resolve()
        except OSError:
            pass
        out.setdefault(str(key), []).append(
            (m.group("code"), m.group("sev"), int(m.group("line"))))
    return out


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
        diags = parse_diagnostics(r.stdout, work_dir=work, real_dir=app_dir)
        return {"repo": repo, "app_dir": str(app_dir), "symbol_version": v,
                "error_clean": r.clean, "n_errors": len(r.errors),
                "error_codes": sorted({c for s, c, _ in r.diagnostics if s == "error"}),
                "n_analyzer_hits": len(r.analyzer_hits),
                "analyzer_rules": sorted({c for _, c in r.analyzer_hits}),
                # {abs source .al path: [[code, severity, line], ...]} for per-member attribution
                "diagnostics_detail": {k: [list(t) for t in v_] for k, v_ in diags.items()}}
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


def _diagnostics_by_path() -> dict[str, list]:
    """Merge every baseline entry's `diagnostics_detail` into one path-keyed map."""
    if not BASELINE.exists():
        return {}
    merged: dict[str, list] = {}
    for r in json.loads(BASELINE.read_text()):
        for k, v in (r.get("diagnostics_detail") or {}).items():
            merged.setdefault(k, []).extend(tuple(t) for t in v)
    return merged


def build_members(only_clean_apps: bool = True) -> None:
    clean = _clean_app_dirs()
    diags_by_path = _diagnostics_by_path()
    n = n_attributed = 0
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
                    for rec in records_for_file(f, repo, root, diags_by_path):
                        fh.write(json.dumps(rec) + "\n")
                        n += 1
                        if rec.get("analyzer_hits") or rec.get("error_hits"):
                            n_attributed += 1
                except Exception as e:  # noqa: BLE001
                    fh.write(json.dumps({"_parse_error": str(e), "path": str(f)}) + "\n")
    print(f"corpus: {n} member records ({n_attributed} with attributed diagnostics) -> {CORPUS}")


def build_baseline_and_corpus_mini(app_dirs: list[Path], out: Path | None = None) -> dict:
    """Self-contained mini pipeline: compile each app in `app_dirs`, attribute every
    diagnostic to the member it falls in, and write member rows (with `error_hits` /
    `analyzer_hits`) to `out` (default `data/corpus.jsonl`). Resumable is not the
    point here — it recomputes the given apps every call."""
    out = out or CORPUS
    diags_by_path: dict[str, list] = {}
    compiled: list[dict] = []
    for app_dir in app_dirs:
        res = _baseline_one((str(app_dir.parent.name) + "/" + app_dir.name, str(app_dir)))
        compiled.append({k: res[k] for k in res if k != "diagnostics_detail"})
        for k, v in (res.get("diagnostics_detail") or {}).items():
            diags_by_path.setdefault(k, []).extend(tuple(t) for t in v)
        print(f"  {app_dir.name}: clean={res.get('error_clean')} "
              f"analyzer_rules={res.get('analyzer_rules')}")
    n = n_attr = 0
    with out.open("w") as fh:
        for app_dir in app_dirs:
            repo = "microsoft/BCApps"
            for f in sorted(app_dir.rglob("*.al")):
                if "/.alpackages/" in str(f):
                    continue
                try:
                    for rec in records_for_file(f, repo, app_dir, diags_by_path):
                        rec["app_dir"] = str(app_dir)   # mini-set only: lets G8 re-open the app
                        fh.write(json.dumps(rec) + "\n")
                        n += 1
                        if rec.get("analyzer_hits") or rec.get("error_hits"):
                            n_attr += 1
                except Exception as e:  # noqa: BLE001
                    fh.write(json.dumps({"_parse_error": str(e), "path": str(f)}) + "\n")
    print(f"mini corpus: {n} members ({n_attr} attributed) -> {out}")
    return {"apps": len(app_dirs), "members": n, "attributed": n_attr, "compiled": compiled}
