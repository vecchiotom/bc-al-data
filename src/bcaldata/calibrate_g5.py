"""Calibrate the G5 mutation catalog: for each mutation, on a deterministic
sample of clean corpus members, record what the AL compiler actually does.

Writes:
  data/g5_calibration.json — {mutation: {sample, applicable, applicability_rate,
      any_new_error, any_new_error_rate, modal_new_code, expected,
      matches_expected, new_code_hist, raw_code_hist}}
  data/g5_calibration.md — per-mutation table (applicability %, any-new-error %,
      modal new code, matches-expected?) + histograms

"New error" = an *extra occurrence* of an error code when compiling the mutated
member versus the pristine one under an identical codeunit wrapper (multiset
difference). Counting occurrences, not the code set, is what lets a mutation
that adds one more AL0118 to a member that already has AL0118 out of context
still register — the wrapper leaves ambient errors (undefined Rec, sibling
calls) that a set difference would mask.

Compilation is the cost. Every distinct snippet (pristine + one per applicable
mutation) is compiled exactly once, in a process pool of cold `al compile`
workers, and results are cached on disk by content hash between runs.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .build_corpus import CORPUS
from .mutations import CATALOG, EXPECTED, apply_mutation
from .verify import _compile_snippet, _wrap_object

DATA = Path.home() / "bc-al-data" / "data"
OUT_JSON = DATA / "g5_calibration.json"
OUT_MD = DATA / "g5_calibration.md"
_CC = DATA / ".cache" / "g5_calibration_snippets"
_CC.mkdir(parents=True, exist_ok=True)

_MODE = os.environ.get("G5_CALIBRATE_MODE", "lsp")  # "lsp" (resident, fast) | "compile" (cold, authoritative)


def _codes_for(al: str) -> list[str]:
    """Error codes for one snippet, disk-cached by content hash.

    Default path is the resident AL server (warm `al_compile`, ~10x a cold
    `al compile`); set G5_CALIBRATE_MODE=compile to force the cold compiler.
    """
    kf = _CC / (hashlib.sha256((_MODE + "|multiset\0" + al).encode()).hexdigest() + ".json")
    if kf.exists():
        return json.loads(kf.read_text())
    if _MODE == "lsp":
        try:
            from .verify import _worker_mcp
            srv = _worker_mcp()
            f = Path(srv.project_dir) / "src" / "Snippet.al"
            codes = sorted(d["code"] for d in srv.diagnostics(f, _wrap_object(al))
                           if d["severity"] == 1 and d["code"])
            kf.write_text(json.dumps(codes))
            return codes
        except Exception:  # noqa: BLE001 - fall back to the authoritative cold compile
            pass
    cr = _compile_snippet(al)
    codes = sorted(c for s, c, _ in cr.diagnostics if s == "error" and c)
    kf.write_text(json.dumps(codes))
    return codes


def _select(n_samples: int) -> list[dict]:
    rows = [json.loads(l) for l in CORPUS.read_text().splitlines()
            if l.strip() and "_parse_error" not in l]
    rows = [r for r in rows
            if r.get("has_body") and not r.get("is_test")
            and 3 <= r.get("body_loc", 0) <= 40
            and r.get("member_kind") in ("procedure", "trigger")
            and "begin" in r.get("body", "")]
    step = max(1, len(rows) // n_samples)
    return rows[::step][:n_samples]


def calibrate(n_samples: int = 80, workers: int = 0) -> dict:
    workers = workers or max(1, (os.cpu_count() or 4) // 2)
    rows = _select(n_samples)

    # build the plan: pristine snippet per row + mutated snippet per applicable mutation
    pristine = {i: r["member_text"] for i, r in enumerate(rows)}
    applied: dict[str, dict[int, str]] = {name: {} for name, _ in CATALOG}
    for name, fn in CATALOG:
        for i, r in enumerate(rows):
            try:
                res = apply_mutation(name, fn, r, None)
            except Exception:  # noqa: BLE001 - odd source: mutation simply skipped
                res = None
            if res is not None:
                applied[name][i] = res[0]

    snippets = sorted({*pristine.values(), *(t for m in applied.values() for t in m.values())})
    print(f"{len(rows)} sampled members, {sum(len(m) for m in applied.values())} mutation applications, "
          f"{len(snippets)} distinct snippets to compile on {workers} workers")

    codes: dict[str, list[str]] = {}
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for al, cs in zip(snippets, ex.map(_codes_for, snippets, chunksize=1)):
            codes[al] = cs
            done += 1
            if done % 20 == 0:
                print(f"  compiled {done}/{len(snippets)}")

    stats: dict[str, dict] = {}
    for name, _ in CATALOG:
        new_hist: collections.Counter = collections.Counter()
        raw_hist: collections.Counter = collections.Counter()
        per_code: collections.Counter = collections.Counter()
        any_new = 0
        appl = applied[name]
        for i, bad_text in appl.items():
            good = collections.Counter(codes[pristine[i]])
            bad = collections.Counter(codes[bad_text])
            raw_hist["|".join(sorted(bad)) or "<none>"] += 1
            delta = bad - good  # Counter subtraction keeps only positive counts
            if delta:
                any_new += 1
                new_hist["|".join(sorted(delta.elements()))] += 1
                for c in delta:
                    per_code[c] += 1
        expected = EXPECTED.get(name, [])
        modal = per_code.most_common(1)[0][0] if per_code else None
        stats[name] = {
            "sample": len(rows),
            "applicable": len(appl),
            "applicability_rate": round(len(appl) / len(rows), 3),
            "any_new_error": any_new,
            "any_new_error_rate": round(any_new / len(appl), 3) if appl else 0.0,
            "modal_new_code": modal,
            "expected": expected,
            "matches_expected": bool(modal and modal in expected),
            "new_code_hist": dict(per_code.most_common()),
            "new_code_combo_hist": dict(new_hist.most_common(8)),
            "raw_code_hist": dict(raw_hist.most_common(6)),
        }
        print(f"{name:26} appl={len(appl):3d}/{len(rows)}  any_new={any_new:3d}  "
              f"modal={modal}  exp={expected}  match={stats[name]['matches_expected']}")

    OUT_JSON.write_text(json.dumps(stats, indent=2))
    _write_md(stats)
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_MD}")
    return stats


def _write_md(stats: dict) -> None:
    sample = next(iter(stats.values()))["sample"]
    lines = [
        "# G5 mutation calibration",
        "",
        f"Sample: {sample} deterministic clean corpus members "
        "(procedure/trigger, 3-40 body LOC), stride-sampled from `data/corpus.jsonl`.",
        "",
        "`new code` = an extra occurrence of an error code for the mutated member "
        "versus the pristine one under an identical `codeunit` wrapper (multiset "
        "difference) — isolates the mutation from the ambient errors a member has "
        "outside its home object.",
        "",
        "| mutation | applicable % | any-new-error % | modal new code | expected | match |",
        "|---|---|---|---|---|---|",
    ]
    for name, s in stats.items():
        lines.append(
            f"| `{name}` | {s['applicability_rate']*100:.0f}% "
            f"| {s['any_new_error_rate']*100:.0f}% "
            f"| {s['modal_new_code'] or '—'} "
            f"| {', '.join(s['expected']) or '—'} "
            f"| {'yes' if s['matches_expected'] else 'no'} |"
        )
    lines += ["", "## New-code histograms (per applied mutation)", ""]
    for name, s in stats.items():
        hist = ", ".join(f"{k}:{v}" for k, v in s["new_code_hist"].items()) or "(none)"
        lines.append(f"- **{name}**: {hist}")
    OUT_MD.write_text("\n".join(lines) + "\n")
