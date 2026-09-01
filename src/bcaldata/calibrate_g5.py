"""Map each G5 mutation to the AL#### error code it actually produces, on a
deterministic sample of clean corpus members. Writes data/g5_calibration.json ."""
from __future__ import annotations
import collections, json
from pathlib import Path

from .build_corpus import CORPUS
from .generators import _MUTATIONS
from .verify import _compile_snippet

OUT = Path.home() / "bc-al-data" / "data" / "g5_calibration.json"


def calibrate(n_samples: int = 120) -> dict:
    rows = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip() and "_parse_error" not in l]
    rows = [r for r in rows if r.get("has_body") and 4 <= r.get("body_loc", 0) <= 20 and not r["is_test"]]
    rows = rows[:: max(1, len(rows) // n_samples)][:n_samples]
    by_mut = collections.defaultdict(collections.Counter)
    for r in rows:
        good = f"{r['signature']}\n{r['body']}"
        for mid, fn in _MUTATIONS:
            res = fn(r["body"])
            if not res:
                continue
            bad = f"{r['signature']}\n{res[0]}"
            if bad == good:
                continue
            cr = _compile_snippet(bad)
            codes = tuple(sorted({c for s, c, _ in cr.diagnostics if s == "error"}))
            by_mut[mid][codes or ("<none>",)] += 1
    result = {mid: {"|".join(k): v for k, v in cnt.most_common()} for mid, cnt in by_mut.items()}
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result
