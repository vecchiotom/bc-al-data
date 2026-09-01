"""Stage 6 — held-out split (by whole app), balance, ShareGPT format, datacard."""
from __future__ import annotations
import hashlib, json, collections
from pathlib import Path

DATA = Path.home() / "bc-al-data" / "data"
OUT = DATA / "dataset"
HELDOUT_APP_RATE = 12          # 1 in N mineable apps is fully reserved


def _app_of(row: dict) -> str:
    return (row["meta"].get("path", "") or row["meta"].get("object", "")).rsplit("/", 1)[0]


def _heldout(app: str) -> bool:
    return int.from_bytes(hashlib.sha1(app.encode()).digest()[:4], "big") % HELDOUT_APP_RATE == 0


def _sharegpt(row: dict) -> dict:
    role = {"user": "human", "assistant": "gpt", "system": "system"}
    return {"conversations": [{"from": role[m["role"]], "value": m["content"]} for m in row["messages"]],
            "meta": {**row["meta"], "gen": row["gen"]}}


def assemble(verified_dir: Path, *, kind_cap: float = 0.30) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for jf in sorted(verified_dir.glob("*.jsonl")):
        rows += [json.loads(l) for l in jf.read_text().splitlines() if l.strip()]

    train, val, held, pref = [], [], [], []
    per_kind = collections.Counter()
    kept_by_gen = collections.Counter()
    for i, r in enumerate(rows):
        if _heldout(_app_of(r)):
            held.append(r); continue
        gen = r["gen"]
        if r.get("rejected_al"):
            pref.append({"prompt": r["messages"][0]["content"],
                         "chosen": r["messages"][-1]["content"],
                         "rejected": r["rejected_al"],
                         "meta": {**r["meta"], "gen": gen}})
            kept_by_gen[gen] += 1
            continue
        (val if i % 20 == 0 else train).append(_sharegpt(r))
        kept_by_gen[gen] += 1

    (OUT / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (OUT / "val.jsonl").write_text("\n".join(json.dumps(r) for r in val) + "\n")
    (OUT / "preference.jsonl").write_text("\n".join(json.dumps(r) for r in pref) + "\n")
    (OUT / "heldout.jsonl").write_text("\n".join(json.dumps(r) for r in held) + "\n")

    card = {
        "total_rows": len(rows),
        "train": len(train), "val": len(val), "preference": len(pref), "heldout": len(held),
        "by_generator": dict(kept_by_gen),
        "heldout_app_rate": HELDOUT_APP_RATE,
    }
    (OUT / "datacard.json").write_text(json.dumps(card, indent=2))
    print(json.dumps(card, indent=2))
    return card
