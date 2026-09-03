"""Stage 6 — held-out split (by whole app), balance, ShareGPT format, datacard."""
from __future__ import annotations
import collections
import hashlib
import json
import random
from pathlib import Path

DATA = Path.home() / "bc-al-data" / "data"
OUT = DATA / "dataset"
HELDOUT_APP_RATE = 12          # 1 in N mineable apps is fully reserved
_VAL_RATE = 20                 # 1 in N non-heldout SFT rows -> validation


def _app_of(row: dict) -> str:
    """The origin app a row belongs to, for the whole-app held-out split. `path`
    is repo-relative (`src/Apps/W1/Foo/App/src/Bar.al`); its directory is a stable
    per-app key. Doc rows (g4) and any row without a path fall back to a constant."""
    p = row["meta"].get("path", "")
    if p and "/" in p:
        return p.rsplit("/", 1)[0]
    return row["meta"].get("object", "") or row["gen"]


def _heldout(app: str) -> bool:
    return int.from_bytes(hashlib.sha1(app.encode()).digest()[:4], "big") % HELDOUT_APP_RATE == 0


def _sharegpt(row: dict) -> dict:
    role = {"user": "human", "assistant": "gpt", "system": "system"}
    return {"conversations": [{"from": role[m["role"]], "value": m["content"]} for m in row["messages"]],
            "meta": {**row["meta"], "gen": row["gen"]}}


def assemble(verified_dir: Path, *, kind_cap: float = 0.35, out_dir: Path | None = None) -> dict:
    """Split `verified_dir/*.jsonl` into train / val / preference / heldout.

    - Whole apps (`sha1(app_dir) % HELDOUT_APP_RATE == 0`) are reserved as `heldout`
      and never contribute to train/val/preference.
    - Rows carrying `rejected_al` become preference triples; the rest are SFT.
    - `kind_cap` bounds any single generator's share of the SFT train set; the
      surplus (lowest-priority by a stable per-row hash) is dropped.
    """
    out = out_dir or OUT
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for jf in sorted(verified_dir.glob("*.jsonl")):
        rows += [json.loads(l) for l in jf.read_text().splitlines() if l.strip()]

    held, pref, sft = [], [], []
    for r in rows:
        if _heldout(_app_of(r)):
            held.append(r)
        elif r.get("rejected_al"):
            pref.append(r)
        else:
            sft.append(r)

    # per-generator cap on the SFT set
    rng_key = lambda r: hashlib.sha1(
        (r["gen"] + r["messages"][-1]["content"]).encode("utf8", "replace")).hexdigest()
    by_gen: dict[str, list] = collections.defaultdict(list)
    for r in sft:
        by_gen[r["gen"]].append(r)
    cap = max(1, int(len(sft) * kind_cap))
    capped, dropped_cap = [], 0
    for gen, grp in by_gen.items():
        grp.sort(key=rng_key)
        capped += grp[:cap]
        dropped_cap += max(0, len(grp) - cap)

    random.Random(0xA1).shuffle(capped)
    train = [_sharegpt(r) for i, r in enumerate(capped) if i % _VAL_RATE != 0]
    val = [_sharegpt(r) for i, r in enumerate(capped) if i % _VAL_RATE == 0]
    preference = [{"prompt": r["messages"][0]["content"],
                   "chosen": r["messages"][-1]["content"],
                   "rejected": r["rejected_al"],
                   "meta": {**r["meta"], "gen": r["gen"]}} for r in pref]

    (out / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (out / "val.jsonl").write_text("\n".join(json.dumps(r) for r in val) + "\n")
    (out / "preference.jsonl").write_text("\n".join(json.dumps(r) for r in preference) + "\n")
    (out / "heldout.jsonl").write_text("\n".join(json.dumps(_sharegpt(r)) for r in held) + "\n")

    card = {
        "total_rows": len(rows),
        "train": len(train), "val": len(val), "preference": len(preference), "heldout": len(held),
        "dropped_to_kind_cap": dropped_cap,
        "by_generator": dict(collections.Counter(r["gen"] for r in capped + pref)),
        "heldout_by_generator": dict(collections.Counter(r["gen"] for r in held)),
        "kind_cap": kind_cap, "heldout_app_rate": HELDOUT_APP_RATE,
    }
    (out / "datacard.json").write_text(json.dumps(card, indent=2))
    print(json.dumps(card, indent=2))
    return card
