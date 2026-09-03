"""Stage 3 — G8: analyzer warning -> clean AL.

Iterates `data/corpus.jsonl` members that carry `analyzer_hits` (attributed in
Stage 2a, see `build_corpus`/`corpus`), asks the ALCops MCP server to apply every
available code fix, and writes:

  data/candidates/g8_warning_clean.jsonl   SFT + preference (original -> fixed)
  data/candidates/g8_review.jsonl          review variant (findings + templates)

Fixes run against a throwaway copy of the whole app (symbols seeded like
`compile_gate.prepare`), so the analyzer sees the real object context and
`apply_fix` resolves the same diagnostics that Stage 2a attributed. Each fixed
member is re-parsed out of the rewritten file; a member whose code is unchanged
still produces a review row.

Requires `app_dir` on the corpus rows (written by
`build_corpus.build_baseline_and_corpus_mini`).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

from . import generators as G
from .alparse import objects
from .compile_gate import prepare

DATA = Path.home() / "bc-al-data" / "data"
CORPUS = DATA / "corpus.jsonl"
CAND = DATA / "candidates"
ERROR_MAP = DATA / "al_error_map.json"

_FIXABLE_PREFIXES = ("AA", "AC", "AW", "DC", "FC", "LC", "PC", "TA", "UI")


def _message_templates() -> dict[str, str]:
    if not ERROR_MAP.exists():
        return {}
    raw = json.loads(ERROR_MAP.read_text())
    return {k: (v.get("message_template") or "") for k, v in raw.items()}


def _corpus_rows(limit: int | None = None) -> list[dict]:
    rows: list[dict] = []
    for line in CORPUS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "_parse_error" in r or not r.get("analyzer_hits"):
            continue
        if r.get("member_kind") != "procedure" or not r.get("has_body"):
            continue
        rows.append(r)
        if limit and len(rows) >= limit:
            break
    return rows


def _member_text(src: bytes, name: str) -> str | None:
    for obj in objects(src):
        for m in obj.members:
            if m.name == name and m.body_start_byte is not None:
                body = src[m.body_start_byte:m.body_end_byte].decode("utf8", "replace")
                return f"{m.signature}\n{body}"
    return None


def _apply_fixes_to_file(mcp, project: str, file_path: str,
                         hit_lines: list[int]) -> list[str]:
    """Apply every available ALCops code fix touching `hit_lines` in `file_path`.
    Re-analyzes between applies (offsets shift); returns the applied rule ids."""
    applied: list[str] = []
    for _ in range(2 * max(1, len(hit_lines)) + 4):
        an = mcp.call_tool_json("analyze", {"projectPath": project, "filePath": file_path})
        diags = an.get("diagnostics", []) if isinstance(an, dict) else []
        want = {ln for ln in hit_lines}
        targets = [d for d in diags
                   if d.get("hasCodeFix")
                   and str(d.get("id", ""))[:2] in _FIXABLE_PREFIXES
                   and any(abs(d.get("startLine", -99) - ln) <= 1 for ln in want)]
        progressed = False
        for d in targets:
            did, line, col = d["id"], d.get("startLine", 1), d.get("startColumn", 1)
            try:
                fixes = mcp.call_tool_json(
                    "get_fixes", {"projectPath": project, "filePath": file_path,
                                  "diagnosticId": did, "line": line, "column": col})
            except Exception:  # noqa: BLE001 - fix listing failed; skip this hit
                continue
            keys = [f.get("equivalenceKey") for f in fixes
                    if isinstance(f, dict) and f.get("equivalenceKey")]
            if not keys:
                continue
            before = Path(file_path).read_text()
            try:
                mcp.call_tool_json(
                    "apply_fix", {"projectPath": project, "filePath": file_path,
                                  "diagnosticId": did, "line": line, "column": col,
                                  "equivalenceKey": keys[0]})
            except Exception:  # noqa: BLE001 - apply failed; leave the hit in place
                continue
            if Path(file_path).read_text() != before:
                applied.append(did)
                progressed = True
                break  # re-analyze
        if not progressed:
            break
    return sorted(set(applied))


def run_g8(limit: int | None = None) -> dict:
    CAND.mkdir(parents=True, exist_ok=True)
    templates = _message_templates()
    rows = _corpus_rows(limit)
    by_app: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_app[r.get("app_dir", "")].append(r)

    try:
        from .mcp_client import ALCopsMcp

        mcp_wrap = ALCopsMcp(timeout=240).start()
        mcp = mcp_wrap.mcp
    except Exception as e:  # noqa: BLE001 - MCP unavailable: review rows only
        print(f"g8: ALCops MCP unavailable ({e}); emitting review rows only")
        mcp_wrap = mcp = None

    n_fix = n_review = 0
    applied_rules: set[str] = set()
    fixed_by_key: dict[tuple[str, str], tuple[str, list[str]]] = {}

    for app_dir, app_rows in by_app.items():
        if mcp is not None and app_dir and Path(app_dir).is_dir():
            work = Path(tempfile.mkdtemp(prefix="bcaldata-g8app-"))
            shutil.rmtree(work)
            try:
                shutil.copytree(app_dir, work)
                try:
                    prepare(work)
                except Exception as e:  # noqa: BLE001 - symbols unavailable for this app
                    print(f"  {Path(app_dir).name}: prepare failed ({e})")
                    work = None
                if work is not None:
                    per_file: dict[str, list[dict]] = defaultdict(list)
                    for r in app_rows:
                        per_file[r["path"]].append(r)
                    for rel, frows in per_file.items():
                        f = work / rel
                        if not f.is_file():
                            continue
                        hit_lines = sorted({h[2] for r in frows for h in r["analyzer_hits"]})
                        applied = _apply_fixes_to_file(mcp, str(work), str(f), hit_lines)
                        if not applied:
                            continue
                        applied_rules.update(applied)
                        new_src = f.read_bytes()
                        for r in frows:
                            mt = _member_text(new_src, r["member_name"])
                            if mt:
                                fixed_by_key[(app_dir, r["path"] + "::" + r["member_name"])] = (mt, applied)
            finally:
                if work is not None:
                    shutil.rmtree(work, ignore_errors=True)

    fix_out = CAND / "g8_warning_clean.jsonl"
    review_out = CAND / "g8_review.jsonl"
    with fix_out.open("w") as ff, review_out.open("w") as rf:
        for r in rows:
            key = (r.get("app_dir", ""), r["path"] + "::" + r["member_name"])
            fixed_text, applied = fixed_by_key.get(key, (None, []))
            for cand in G.g8_warning_clean(r, fixed_text=fixed_text, applied_rules=applied):
                ff.write(json.dumps(cand) + "\n")
                n_fix += 1
            for cand in G.g8_review(r, message_templates=templates):
                rf.write(json.dumps(cand) + "\n")
                n_review += 1

    if mcp_wrap is not None:
        mcp_wrap.close()

    stats = {"members": len(rows), "g8_warning_clean": n_fix, "g8_review": n_review,
             "rules_with_working_apply_fix": sorted(applied_rules)}
    print(f"g8: {stats}")
    return stats


if __name__ == "__main__":
    run_g8()
