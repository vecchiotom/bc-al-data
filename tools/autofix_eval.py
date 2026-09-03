"""Validate the AL auto-fixer against the labelled G5 broken/fixed set — no model.

Each `data/candidates/g5_error_fix.jsonl` row is `rejected_al` (a mutated,
non-compiling member) + `target_al` (the clean original) + `mutation` (the label).
For a sample we run `autofix(rejected_al, <compile diags>)` and score, per
mutation class:
  - repaired  : the fix compiles error-clean
  - exact     : the fix equals `target_al` (whitespace-normalised)
  - unfixable : autofix returned no fix

Slow: one `al compile` per pass per sample (~10-45s). Use `--n` small first, or
run under nohup and poll `data/autofix_eval.json`.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import time
from pathlib import Path

from bcaldata.autofix import autofix, _compile, _clean

DATA = Path.home() / "bc-al-data" / "data"
SRC = DATA / "candidates" / "g5_error_fix.jsonl"
OUT = DATA / "autofix_eval.json"


def _norm(s: str) -> str:
    return "\n".join(ln.rstrip() for ln in s.strip().splitlines())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mutation", default=None, help="restrict to one mutation class")
    args = ap.parse_args()

    rows = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
    if args.mutation:
        rows = [r for r in rows if r["mutation"] == args.mutation]
    random.Random(args.seed).shuffle(rows)
    rows = rows[: args.n]

    by: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    methods: collections.Counter = collections.Counter()
    reasons: collections.Counter = collections.Counter()
    t0 = time.time()

    for i, r in enumerate(rows, 1):
        mut = r["mutation"]
        by[mut]["total"] += 1
        broken, target = r["rejected_al"], r["target_al"]
        try:
            fixed, method = autofix(broken, [])
        except Exception as e:  # noqa: BLE001
            fixed, method = None, f"error:{e}"
        if fixed is None:
            by[mut]["unfixable"] += 1
            reasons[method] += 1
        else:
            methods[method] += 1
            clean = _clean(_compile(fixed, None))
            if clean:
                by[mut]["repaired"] += 1
                if _norm(fixed) == _norm(target):
                    by[mut]["exact"] += 1
            else:
                by[mut]["repaired_dirty"] += 1
        if i % 10 == 0:
            print(f"  {i}/{len(rows)}  {time.time() - t0:.0f}s", flush=True)

    result = {
        "n": len(rows), "seconds": round(time.time() - t0, 1),
        "per_mutation": {m: dict(c) for m, c in sorted(by.items())},
        "methods": dict(methods), "unfixable_reasons": dict(reasons),
    }
    OUT.write_text(json.dumps(result, indent=2))

    print(f"\nautofix eval  n={len(rows)}  {result['seconds']}s  -> {OUT}\n")
    hdr = f"{'mutation':<24}{'n':>5}{'repaired':>10}{'exact':>8}{'unfix':>8}"
    print(hdr)
    print("-" * len(hdr))
    for m, c in sorted(by.items()):
        tot = c["total"] or 1
        print(f"{m:<24}{c['total']:>5}{c['repaired'] / tot:>9.0%}"
              f"{c['exact'] / tot:>8.0%}{c['unfixable'] / tot:>8.0%}")
    tot = sum(c["total"] for c in by.values()) or 1
    rep = sum(c["repaired"] for c in by.values())
    exa = sum(c["exact"] for c in by.values())
    unf = sum(c["unfixable"] for c in by.values())
    print("-" * len(hdr))
    print(f"{'ALL':<24}{tot:>5}{rep / tot:>9.0%}{exa / tot:>8.0%}{unf / tot:>8.0%}")
    print("\nmethods:", dict(methods))
    print("unfixable reasons:", dict(reasons))


if __name__ == "__main__":
    main()
