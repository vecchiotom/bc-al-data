"""Stage 5 — dedup + decontamination + license gate."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from datasketch import MinHash, MinHashLSH

from .decontam import load as load_blocklist, is_contaminated
from .sources import SOURCES, ALLOWED_SPDX

_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s or "").strip().lower()


def _shingles(s: str, k: int = 5) -> set[str]:
    toks = _norm(s).split()
    return {" ".join(toks[i:i + k]) for i in range(max(1, len(toks) - k + 1))}


def _mh(s: str) -> MinHash:
    m = MinHash(num_perm=64)
    for sh in _shingles(s):
        m.update(sh.encode())
    return m


_LICENSE_BY_REPO = {s.url.split("github.com/")[-1]: s.spdx for s in SOURCES}


def filter_file(in_jsonl: Path, out_jsonl: Path, *, jaccard: float = 0.8) -> dict:
    bl = load_blocklist()
    rows = [json.loads(l) for l in in_jsonl.read_text().splitlines() if l.strip()]
    seen_exact: set[str] = set()
    lsh = MinHashLSH(threshold=jaccard, num_perm=64)
    kept = []
    drop = {"exact": 0, "near": 0, "contam_path": 0, "contam_prompt": 0, "license": 0}
    bl_prompt_norm = {_norm(p) for p in bl["prompts"]}

    for i, r in enumerate(rows):
        repo = r["meta"].get("repo", "")
        if repo in _LICENSE_BY_REPO and _LICENSE_BY_REPO[repo] not in ALLOWED_SPDX and "docs" not in repo.lower() \
           and not repo.startswith("MicrosoftDocs"):
            drop["license"] += 1; continue
        path = r["meta"].get("path", "")
        if path and is_contaminated(path, bl):
            drop["contam_path"] += 1; continue
        prompt_norm = _norm(r["messages"][0]["content"])
        if prompt_norm in bl_prompt_norm:
            drop["contam_prompt"] += 1; continue
        # preference pairs (g5/g7/g8-clean) share one `target_al` across many broken
        # variants of the same member — dedup on the prompt + rejected side instead.
        if r.get("rejected_al"):
            text = r["messages"][0]["content"] + "\n" + r["rejected_al"]
        else:
            text = (r.get("target_al") or "") + "\n" + r["messages"][-1]["content"]
        h = hashlib.sha256(_norm(text).encode()).hexdigest()
        if h in seen_exact:
            drop["exact"] += 1; continue
        seen_exact.add(h)
        m = _mh(text)
        if lsh.query(m):
            drop["near"] += 1; continue
        lsh.insert(f"r{i}", m)
        kept.append(r)

    out_jsonl.write_text("\n".join(json.dumps(r) for r in kept) + ("\n" if kept else ""))
    stats = {"in": len(rows), "kept": len(kept), **{f"drop_{k}": v for k, v in drop.items()}}
    print(f"filter {in_jsonl.name}: {stats}")
    return stats
