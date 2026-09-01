"""Stage 3 driver — run generators over the corpus, write candidates/<gen>.jsonl.

Deterministic generators run locally. G3 paraphrase and G7 rollouts call the
local vLLM model (batched). Everything is append-resumable by (gen, provenance).
"""
from __future__ import annotations
import json, os
from pathlib import Path

from .build_corpus import CORPUS, BASELINE
from . import generators as G

DATA = Path.home() / "bc-al-data" / "data"
CAND = DATA / "candidates"
CAND.mkdir(parents=True, exist_ok=True)

DETERMINISTIC = {
    "g1_fim": G.g1_fim, "g2_sig2body": G.g2_sig2body, "g5_error_fix": G.g5_error_fix,
}


def _corpus_rows():
    for line in CORPUS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "_parse_error" not in r:
            yield r


def run_deterministic(limit_per_gen: int | None = None) -> dict:
    counts = {}
    for name, fn in DETERMINISTIC.items():
        out = CAND / f"{name}.jsonl"
        n = 0
        with out.open("w") as fh:
            for rec in _corpus_rows():
                for cand in fn(rec):
                    fh.write(json.dumps(cand) + "\n")
                    n += 1
                    if limit_per_gen and n >= limit_per_gen:
                        break
                if limit_per_gen and n >= limit_per_gen:
                    break
        counts[name] = n
    # object-level G6
    from .alparse import objects
    from .sources import SOURCES, VENDOR
    n6 = 0
    with (CAND / "g6_spec2object.jsonl").open("w") as fh:
        for s in SOURCES:
            if s.role != "mine":
                continue
            root = VENDOR / s.key
            for f in sorted((root / s.subdir).rglob("*.al")):
                try:
                    src = f.read_bytes()
                except OSError:
                    continue
                for obj in objects(src):
                    for cand in G.object_level_g6(obj.text, obj.kind, obj.obj_id, obj.name,
                                                  s.url.split("github.com/")[-1], str(f.relative_to(root))):
                        fh.write(json.dumps(cand) + "\n")
                        n6 += 1
    counts["g6_spec2object"] = n6
    print("deterministic candidates:", counts)
    return counts


def run_g3(limit: int | None = None) -> int:
    from .llm import chat
    out = CAND / "g3_explain.jsonl"
    n = 0
    with out.open("w") as fh:
        for rec in _corpus_rows():
            for base in G.g3_explain(rec):
                try:
                    cand = G.g3_paraphrase(base, chat)
                except Exception as e:  # noqa: BLE001
                    cand = {**base, "meta": {**base["meta"], "paraphrase_error": str(e)}}
                fh.write(json.dumps(cand) + "\n")
                n += 1
            if limit and n >= limit:
                break
    print(f"g3 candidates (model-paraphrased): {n}")
    return n


def run_g4() -> int:
    from .sources import SOURCES, VENDOR
    out = CAND / "g4_docqa.jsonl"
    n = 0
    with out.open("w") as fh:
        for s in SOURCES:
            if s.role != "docs":
                continue
            root = VENDOR / s.key / s.subdir
            for md in sorted(root.rglob("*.md")):
                try:
                    txt = md.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for cand in G.g4_docqa(md.relative_to(VENDOR / s.key), txt):
                    fh.write(json.dumps(cand) + "\n")
                    n += 1
    print(f"g4 candidates: {n}")
    return n


def run_g7(k: int = 8, limit_probes: int | None = 400) -> int:
    """Sample the current model on real prompts; keep non-compiling completions as hard negatives."""
    from .llm import chat
    from .verify import _compile_snippet
    out = CAND / "g7_hard_negative.jsonl"
    n = probes = 0
    with out.open("w") as fh:
        for rec in _corpus_rows():
            pp = G.g7_probe_prompts(rec)
            if not pp:
                continue
            for probe in pp:
                probes += 1
                for _ in range(k):
                    try:
                        comp = chat(probe["messages"], temperature=0.9, reasoning="low", max_tokens=700)
                    except Exception:  # noqa: BLE001
                        continue
                    al = _extract_al(comp)
                    if not al:
                        continue
                    r = _compile_snippet(al)
                    pair = G.g7_from_rollout(probe, al, r)
                    if pair:
                        fh.write(json.dumps(pair) + "\n")
                        n += 1
                        break  # one hard negative per probe is enough
            if limit_probes and probes >= limit_probes:
                break
    print(f"g7 hard negatives: {n} from {probes} probes")
    return n


def _extract_al(text: str) -> str | None:
    import re
    m = re.search(r"```al\s*(.+?)```", text, re.S) or re.search(r"```\s*(.+?)```", text, re.S)
    return m.group(1).strip() if m else None
