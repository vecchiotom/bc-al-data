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
import os
import re
import shutil
import tempfile
from pathlib import Path

from .alparse import objects
from .compile_gate import compile_app, pin_runtime, seed_alpackages, symbol_version
from .sources import VENDOR
from .verify import _shared_alpackages


def _seed_shared(work: Path) -> None:
    """Point `.alpackages` at the process-wide shared symbol set (one seeded dir,
    every worktree symlinks it) so 350 symbol packages stay in the page cache
    instead of being re-read from the 9 GB artifact per compile."""
    alp = work / ".alpackages"
    if alp.is_symlink() or alp.exists():
        return
    alp.symlink_to(_shared_alpackages())


DATA = Path.home() / "bc-al-data" / "data"
CACHE = Path.home() / "bc-al-data" / ".cache" / "verify"
CACHE.mkdir(parents=True, exist_ok=True)
_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s or "").strip()


def _link_tree(src: Path, dst: Path) -> None:
    """Populate `dst` with hardlinks to every file under `src` (dirs recreated),
    skipping `.alpackages`, build outputs, and VCS dirs. Near-instant vs copytree;
    the caller must `unlink()` a file before rewriting it so the real source is
    never touched. Falls back to copy across filesystem boundaries."""
    skip = {".alpackages", ".git", ".vscode", "_compile_out.app"}
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            if f in skip or f.endswith(".app"):
                continue
            s, d = Path(root) / f, dst / rel / f
            try:
                os.link(s, d)
            except OSError:
                shutil.copy2(s, d)


def _write_verdict(kf: Path, verdict: dict) -> None:
    """Atomic cache write — workers read these concurrently; a torn file breaks json."""
    tmp = kf.with_suffix(f".{id(verdict):x}.tmp")
    tmp.write_text(json.dumps(verdict))
    tmp.replace(kf)


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
        _BASELINE = {}
        for r in rows:
            # index under both the recorded path and its symlink-resolved form —
            # `build_baselines` keys on `vendor/bcapps/...`, verify resolves to
            # `vendor/BCApps/...`.
            _BASELINE[r["app_dir"]] = r
            try:
                _BASELINE[str(Path(r["app_dir"]).resolve())] = r
            except OSError:
                pass
    return _BASELINE


def _sig_key(s: str) -> str:
    """Normalized signature up to the parameter list, so overloads compare distinctly
    but `internal procedure`/attribute/whitespace noise does not."""
    s = _WS.sub(" ", s or "").strip().lower()
    s = re.sub(r"^\s*(local |internal |protected )*procedure\s+", "", s)
    return s


def _find_member_range(src: bytes, member_name: str,
                       signature: str | None = None) -> tuple[int, int] | None:
    matches = [(m.start_byte, m.end_byte, getattr(m, "signature", ""))
               for obj in objects(src) for m in obj.members if m.name == member_name]
    if not matches:
        return None
    if signature and len(matches) > 1:
        want = _sig_key(signature)
        for s, e, sig in matches:
            if _sig_key(sig) == want:
                return s, e
    return matches[0][0], matches[0][1]


def _key(cand: dict) -> str:
    prompt = (cand.get("messages") or [{}])[0].get("content", "")
    return "inapp-" + hashlib.sha256(
        (cand["gen"] + "\0" + (cand.get("target_al") or "") + "\0"
         + (cand.get("rejected_al") or "") + "\0" + (cand["meta"].get("path") or "")
         + "\0" + prompt).encode()
    ).hexdigest()


def _compile_with(app_dir: Path, file_rel: str, member_name: str, new_text: str,
                  version: str, signature: str | None = None) -> "object":
    """Worktree copy of `app_dir`, replace `member_name` in `file_rel` with `new_text`, compile."""
    work = Path(tempfile.mkdtemp(prefix="bcaldata-inapp-"))
    try:
        _link_tree(app_dir, work)
        cands = list(work.rglob(Path(file_rel).name))   # file_rel is repo-relative
        if not cands:
            raise FileNotFoundError(file_rel)
        target = cands[0]
        src = target.read_bytes()
        rng = _find_member_range(src, member_name, signature)
        if rng is None:
            raise LookupError(f"member {member_name} not in {target.name}")
        target.unlink()                         # break the hardlink before rewriting
        target.write_bytes(src[:rng[0]] + new_text.encode() + src[rng[1]:])
        _seed_shared(work)
        pin_runtime(work)
        return compile_app(work, version, analyzers=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def verify_one_inapp(cand: dict) -> dict | None:
    kf = CACHE / f"{_key(cand)}.json"
    if kf.is_file():
        try:
            v = json.loads(kf.read_text())
        except (json.JSONDecodeError, OSError):
            v = None
        if v is not None:
            return {**cand, "verify": v} if v["kept"] else None

    meta = cand["meta"]
    repo, rel, member = meta.get("repo", ""), meta.get("path", ""), meta.get("member", "")
    sig = meta.get("signature")
    gen = cand["gen"]
    verdict: dict = {"kept": False, "reason": "", "via": "inapp"}

    # text-only targets never compile
    if gen in ("g3_explain", "g4_docqa", "g8_review") or cand.get("target_al") is None:
        verdict = {"kept": True, "reason": "text target", "via": "none"}
        _write_verdict(kf, verdict)
        return {**cand, "verify": verdict}

    root = _repo_root(repo)
    need_member = gen != "g6_spec2object"   # g6 is object-level; meta carries `object`, no member
    if root is None or not rel or (need_member and not member):
        verdict["reason"] = f"unresolvable origin (repo={repo} path={bool(rel)} member={bool(member)})"
        _write_verdict(kf, verdict)
        return None
    app_dir = _app_dir(root / rel)
    if app_dir is None:
        verdict["reason"] = "no app.json above origin file"
        _write_verdict(kf, verdict)
        return None

    base = _baseline().get(str(app_dir))
    app_baseline_clean = bool(base and base.get("error_clean"))
    version = (base or {}).get("symbol_version") or symbol_version(app_dir, "28.0")

    on_disk = None
    try:
        rng = _find_member_range((root / rel).read_bytes(), member, sig)
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
            r = _compile_with(app_dir, rel, member, cand["target_al"], version, sig)
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
            r_bad = _compile_with(app_dir, rel, member, cand["rejected_al"], version, sig)
            codes = sorted({c for s, c, _ in r_bad.diagnostics if s == "error"})
            # g7's `chosen` is a machine repair of model output, not verbatim source —
            # it must actually compile. g5's is the verbatim original (baseline-clean).
            good_clean = True
            if gen == "g7_hard_negative" and _norm(cand.get("target_al") or "") != _norm(on_disk or ""):
                good_clean = _compile_with(app_dir, rel, member, cand["target_al"], version, sig).clean
            verdict = {"kept": (not r_bad.clean) and good_clean,
                       "reason": f"bad_clean={r_bad.clean} good_clean={good_clean}",
                       "via": "inapp", "symbol_version": version, "error_codes": codes}

    _write_verdict(kf, verdict)
    return {**cand, "verify": verdict} if verdict["kept"] else None


def _resolve_origin(cand: dict) -> tuple[Path, Path, str, str] | None:
    """(app_dir, origin_file, file_rel, symbol_version) for a candidate, or None."""
    meta = cand["meta"]
    root = _repo_root(meta.get("repo", ""))
    rel, member = meta.get("path", ""), meta.get("member", "")
    if root is None or not rel or not member:
        return None
    app_dir = _app_dir(root / rel)
    if app_dir is None:
        return None
    base = _baseline().get(str(app_dir))
    version = (base or {}).get("symbol_version") or symbol_version(app_dir, "28.0")
    return app_dir, root / rel, rel, version


def verify_g5_group(app_dir_str: str, version: str, cands: list[dict]) -> list[dict]:
    """Verify every g5/g7 candidate that originates in one app, reusing a single
    seeded worktree: copy + seed once, then per candidate swap the member, compile,
    restore. A candidate is kept when the app compiled clean at baseline but does
    NOT with `rejected_al` in place. Per-candidate verdicts are still cached by `_key`."""
    app_dir = Path(app_dir_str)
    base = _baseline().get(app_dir_str)
    if not (base and base.get("error_clean")):
        for c in cands:
            _CACHE_WRITE(c, {"kept": False, "reason": "origin app baseline not clean", "via": "inapp"})
        return []

    pending = []
    out: list[dict] = []
    for c in cands:
        kf = CACHE / f"{_key(c)}.json"
        v = None
        if kf.is_file():
            try:
                v = json.loads(kf.read_text())
            except (json.JSONDecodeError, OSError):
                v = None
        if v is None:
            pending.append(c)
        elif v["kept"]:
            out.append({**c, "verify": v})
    if not pending:
        return out

    work = Path(tempfile.mkdtemp(prefix="bcaldata-g5grp-"))
    try:
        _link_tree(app_dir, work)
        _seed_shared(work)
        pin_runtime(work)
        by_file: dict[str, list[dict]] = {}
        for c in pending:
            by_file.setdefault(Path(c["meta"]["path"]).name, []).append(c)
        for fname, group in by_file.items():
            hits = list(work.rglob(fname))
            if not hits:
                for c in group:
                    _CACHE_WRITE(c, {"kept": False, "reason": f"origin file {fname} not in worktree"})
                continue
            target = hits[0]
            original = target.read_bytes()
            target.unlink()                     # break the hardlink to the real source
            for c in group:
                member, sig = c["meta"]["member"], c["meta"].get("signature")
                rng = _find_member_range(original, member, sig)
                if rng is None:
                    _CACHE_WRITE(c, {"kept": False, "reason": f"member {member} not found"})
                    continue
                target.write_bytes(original[:rng[0]] + c["rejected_al"].encode() + original[rng[1]:])
                r = compile_app(work, version, analyzers=False)
                codes = sorted({x for s, x, _ in r.diagnostics if s == "error"})
                v = {"kept": not r.clean, "reason": f"bad_clean={r.clean}", "via": "inapp-batch",
                     "symbol_version": version, "error_codes": codes}
                _CACHE_WRITE(c, v)
                if v["kept"]:
                    out.append({**c, "verify": v})
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


def _CACHE_WRITE(cand: dict, verdict: dict) -> None:
    verdict.setdefault("via", "inapp")
    _write_verdict(CACHE / f"{_key(cand)}.json", verdict)


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
