"""Stage 4, corrected — verify a candidate by compiling it IN its origin app.

The old snippet-wrapper path (`verify._compile_snippet`) fails for almost every
real member: a procedure yanked out of its object references sibling globals
(`Rec`, other procedures, module vars) that don't resolve in a bare wrapper, so
even verbatim BCApps code "doesn't compile". The fix is BC-Bench's compile-proxy
approach: drop the candidate text back into a worktree copy of its real app at
the member's exact byte range and compile the whole app.

- positive generators (g1/g2/g6): the app must compile error-clean with the
  candidate text in place. When the candidate == the original member and the app
  baseline is already clean (`data/app_baseline.json`), that is asserted without
  a recompile (fast path).
- g5/g7 pairs: the app must NOT compile clean with `rejected_al` in place, and
  (baseline) IS clean with the original. The emitted error codes are recorded.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

from .alparse import objects
from .compile_gate import compile_app, pin_runtime, seed_alpackages, symbol_version
from .sources import VENDOR

DATA = Path.home() / "bc-al-data" / "data"
CACHE = Path.home() / "bc-al-data" / ".cache" / "verify"
CACHE.mkdir(parents=True, exist_ok=True)
_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s or "").strip()


def _repo_root(repo: str) -> Path | None:
    # meta.repo is like "microsoft/BCApps"; sources key is the lowercased last segment
    for cand in (repo.split("/")[-1].lower(), repo.split("/")[-1]):
        p = VENDOR / cand
        if p.exists():
            return p.resolve()
    return None


def _app_dir(file_path: Path) -> Path | None:
    for anc in file_path.parents:
        if (anc / "app.json").is_file():
            return anc
        if anc == anc.parent:
            break
    return None


_BASELINE: dict[str, dict] | None = None


def _baseline() -> dict[str, dict]:
    global _BASELINE
    if _BASELINE is None:
        f = DATA / "app_baseline.json"
        rows = json.loads(f.read_text()) if f.is_file() else []
        _BASELINE = {r["app_dir"]: r for r in rows}
    return _BASELINE


def _find_member_range(src: bytes, member_name: str) -> tuple[int, int] | None:
    for obj in objects(src):
        for m in obj.members:
            if m.name == member_name:
                return m.start_byte, m.end_byte
    return None


def _key(cand: dict) -> str:
    return "inapp-" + hashlib.sha256(
        (cand["gen"] + "\0" + (cand.get("target_al") or "") + "\0"
         + (cand.get("rejected_al") or "") + "\0" + (cand["meta"].get("path") or "")).encode()
    ).hexdigest()


def _compile_with(app_dir: Path, file_rel: str, member_name: str, new_text: str,
                  version: str) -> "object":
    """Worktree copy of `app_dir`, replace `member_name` in `file_rel` with `new_text`, compile."""
    work = Path(tempfile.mkdtemp(prefix="bcaldata-inapp-"))
    try:
        shutil.copytree(app_dir, work, dirs_exist_ok=True, symlinks=False,
                        ignore=shutil.ignore_patterns(".alpackages", "*.app", "_compile_out.app"))
        target = work / Path(file_rel).name if (work / Path(file_rel).name).is_file() else work / file_rel
        if not target.is_file():
            # locate by basename anywhere in the worktree
            cands = list(work.rglob(Path(file_rel).name))
            if not cands:
                raise FileNotFoundError(file_rel)
            target = cands[0]
        src = target.read_bytes()
        rng = _find_member_range(src, member_name)
        if rng is None:
            raise LookupError(f"member {member_name} not in {target.name}")
        target.write_bytes(src[:rng[0]] + new_text.encode() + src[rng[1]:])
        seed_alpackages(work, version)
        pin_runtime(work)
        return compile_app(work, version, analyzers=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def verify_one_inapp(cand: dict) -> dict | None:
    kf = CACHE / f"{_key(cand)}.json"
    if kf.is_file():
        v = json.loads(kf.read_text())
        return {**cand, "verify": v} if v["kept"] else None

    meta = cand["meta"]
    repo, rel, member = meta.get("repo", ""), meta.get("path", ""), meta.get("member", "")
    gen = cand["gen"]
    verdict: dict = {"kept": False, "reason": "", "via": "inapp"}

    # text-only targets never compile
    if gen in ("g3_explain", "g4_docqa", "g8_review") or cand.get("target_al") is None:
        verdict = {"kept": True, "reason": "text target", "via": "none"}
        kf.write_text(json.dumps(verdict))
        return {**cand, "verify": verdict}

    root = _repo_root(repo)
    if root is None or not rel or not member:
        verdict["reason"] = f"unresolvable origin (repo={repo} path={bool(rel)} member={bool(member)})"
        kf.write_text(json.dumps(verdict))
        return None
    app_dir = _app_dir(root / rel)
    if app_dir is None:
        verdict["reason"] = "no app.json above origin file"
        kf.write_text(json.dumps(verdict))
        return None

    base = _baseline().get(str(app_dir))
    app_baseline_clean = bool(base and base.get("error_clean"))
    version = (base or {}).get("symbol_version") or symbol_version(app_dir, "28.0")

    on_disk = None
    try:
        rng = _find_member_range((root / rel).read_bytes(), member)
        if rng is not None:
            on_disk = (root / rel).read_bytes()[rng[0]:rng[1]].decode("utf8", "replace")
    except OSError:
        pass

    if gen in ("g1_fim", "g2_sig2body"):
        # candidate is (today) the verbatim original -> clean iff the app baseline is clean
        if on_disk is not None and _norm(on_disk) == _norm(cand["target_al"]) and app_baseline_clean:
            verdict = {"kept": True, "reason": "verbatim original in baseline-clean app",
                       "via": "baseline", "symbol_version": version}
        else:
            r = _compile_with(app_dir, rel, member, cand["target_al"], version)
            verdict = {"kept": r.clean, "reason": f"inapp clean={r.clean} errs={r.errors[:3]}",
                       "via": "inapp", "symbol_version": version,
                       "error_codes": sorted({c for s, c, _ in r.diagnostics if s == "error"})}
    elif gen == "g6_spec2object":
        # target is the verbatim original object, already compiled inside its app
        try:
            on_disk_file = (root / rel).read_text("utf8", "replace")
        except OSError:
            on_disk_file = ""
        if _norm(cand["target_al"]) in _norm(on_disk_file) and app_baseline_clean:
            verdict = {"kept": True, "reason": "verbatim object in baseline-clean app",
                       "via": "baseline", "symbol_version": version}
        else:
            # model-authored object: compile in a fresh minimal app (free id range)
            r = _compile_object_in_fresh_app(cand["target_al"], version)
            verdict = {"kept": r.clean, "reason": f"object fresh-app clean={r.clean}",
                       "via": "fresh-app", "symbol_version": version}
    elif gen in ("g5_error_fix", "g7_hard_negative"):
        if not app_baseline_clean:
            verdict["reason"] = "origin app baseline not clean; cannot attribute the break"
        else:
            r_bad = _compile_with(app_dir, rel, member, cand["rejected_al"], version)
            codes = sorted({c for s, c, _ in r_bad.diagnostics if s == "error"})
            verdict = {"kept": not r_bad.clean, "reason": f"bad_clean={r_bad.clean}",
                       "via": "inapp", "symbol_version": version, "error_codes": codes}

    kf.write_text(json.dumps(verdict))
    return {**cand, "verify": verdict} if verdict["kept"] else None


_FRESH_APP_JSON = {
    "id": "00000000-0000-4000-8000-0000000f8e5b", "name": "bcaldata g6 verify",
    "publisher": "bcaldata", "version": "1.0.0.0", "platform": "28.0.0.0",
    "application": "28.0.0.0", "runtime": "17.0",
    "idRanges": [{"from": 90000, "to": 99999}], "features": ["NoImplicitWith"],
}


def _compile_object_in_fresh_app(obj_al: str, version: str) -> "object":
    """Compile one self-contained object in a throwaway app with a free id range.
    The object id is remapped into 90000-99999 so it never collides."""
    remapped = re.sub(r"^(\s*(?:table|page|enum|report|query|xmlport|codeunit|interface)\s+)\d+",
                      lambda m: m.group(1) + "90000", obj_al, count=1, flags=re.I | re.M)
    work = Path(tempfile.mkdtemp(prefix="bcaldata-g6-"))
    try:
        (work / "app.json").write_text(json.dumps(_FRESH_APP_JSON))
        (work / "src").mkdir()
        (work / "src" / "Obj.al").write_text(remapped)
        seed_alpackages(work, version, build_from_source=["bcaldata g6 verify"])
        return compile_app(work, version, analyzers=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)
