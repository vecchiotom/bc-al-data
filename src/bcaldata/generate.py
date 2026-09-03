"""Stage 3 driver — run generators over the corpus, write candidates/<gen>.jsonl.

Deterministic generators run locally. G3 paraphrase and G7 rollouts call the
local vLLM model (batched). Everything is append-resumable by (gen, provenance).
"""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path

from .build_corpus import CORPUS, BASELINE
from . import generators as G


def _stable_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf8", "replace")).hexdigest()

DATA = Path.home() / "bc-al-data" / "data"
CAND = DATA / "candidates"
CAND.mkdir(parents=True, exist_ok=True)

DETERMINISTIC = {
    "g1_fim": G.g1_fim, "g2_sig2body": G.g2_sig2body, "g5_error_fix": G.g5_error_fix,
}

# G5 needs one whole-app compile per mutated member. These two apps are large and
# slow to compile (~30-40 s each) and a broken-semicolon pair from them teaches
# nothing a pair from a small app doesn't — they are skipped for G5 only.
_G5_SLOW_APPS = ("Subscription Billing", "PowerBIReports")


def _corpus_rows():
    for line in CORPUS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "_parse_error" not in r:
            yield r


def run_deterministic(limit_per_gen: int | None = None,
                      g5_per_mutation: int | None = 600,
                      g5_per_file: int | None = 6,
                      g5_per_app: int | None = 150) -> dict:
    """Deterministic generators over the corpus.

    G5 is capped three ways so the verify compile budget stays bounded and no
    single app dominates: `g5_per_mutation` per mutation class, `g5_per_file` per
    origin `.al` file, `g5_per_app` per app dir (Subscription Billing and
    PowerBIReports are large and slow to compile, and held ~55% of G5 uncapped).
    Members are taken in ascending text-hash order; None on any disables it.
    """
    counts = {}
    for name, fn in DETERMINISTIC.items():
        out = CAND / f"{name}.jsonl"
        n = 0
        per_mut: dict[str, int] = {}
        per_file: dict[str, int] = {}
        per_app: dict[str, int] = {}
        rows = list(_corpus_rows())
        if name == "g5_error_fix" and (g5_per_mutation or g5_per_file):
            rows.sort(key=lambda r: _stable_hash(r.get("member_text", "")))
        with out.open("w") as fh:
            for rec in rows:
                for cand in fn(rec):
                    if name == "g5_error_fix":
                        mid = cand.get("mutation", "")
                        path = cand["meta"].get("path", "")
                        app = "/".join(path.split("/")[:5])   # .../<Area>/<App>/<sub>
                        if any(s in path for s in _G5_SLOW_APPS):
                            continue
                        if g5_per_mutation and per_mut.get(mid, 0) >= g5_per_mutation:
                            continue
                        if g5_per_file and per_file.get(path, 0) >= g5_per_file:
                            continue
                        if g5_per_app and per_app.get(app, 0) >= g5_per_app:
                            continue
                        per_mut[mid] = per_mut.get(mid, 0) + 1
                        per_file[path] = per_file.get(path, 0) + 1
                        per_app[app] = per_app.get(app, 0) + 1
                    fh.write(json.dumps(cand) + "\n")
                    n += 1
                    if limit_per_gen and n >= limit_per_gen:
                        break
                if limit_per_gen and n >= limit_per_gen:
                    break
        counts[name] = n
    # object-level G6 — restricted to files under an error-clean app so the
    # verbatim-object verdict resolves on the instant baseline fast path.
    from .alparse import objects
    from .build_corpus import _clean_app_dirs
    from .sources import SOURCES, VENDOR
    clean_apps = _clean_app_dirs()

    def _under_clean_app(f: Path) -> bool:
        for anc in f.parents:
            if (anc / "app.json").is_file():
                return str(anc) in clean_apps
        return False

    n6 = 0
    with (CAND / "g6_spec2object.jsonl").open("w") as fh:
        for s in SOURCES:
            if s.role != "mine":
                continue
            root = VENDOR / s.key
            for f in sorted((root / s.subdir).rglob("*.al")):
                if not _under_clean_app(f):
                    continue
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
    from collections import Counter

    from .sources import SOURCES, VENDOR
    out = CAND / "g4_docqa.jsonl"
    n = 0
    by_category: Counter[str] = Counter()
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
                    parts = cand["meta"]["path"].split("/")
                    by_category[parts[2] if len(parts) > 3 else "(concepts)"] += 1
    print(f"g4 candidates: {n}")
    for cat, c in by_category.most_common():
        print(f"  developer/{cat}: {c}")
    return n


def run_g7(k: int = 8, limit_probes: int | None = 400) -> int:
    """Sample the current model on real prompts; keep non-compiling completions as hard negatives."""
    from .llm import chat
    from .autofix import autofix
    from .verify_inapp import _compile_with, _resolve_origin
    out = CAND / "g7_hard_negative.jsonl"
    n = probes = 0
    with out.open("w") as fh:
        for rec in _corpus_rows():
            pp = G.g7_probe_prompts(rec)
            if not pp:
                continue
            for probe in pp:
                origin = _resolve_origin({"meta": probe["meta"], "gen": "g7_hard_negative"})
                if origin is None:
                    continue
                app_dir, _, rel, version = origin
                member, sig = probe["meta"].get("member", ""), probe["meta"].get("signature")
                probes += 1
                for _ in range(k):
                    try:
                        comp = chat(probe["messages"], temperature=0.9, reasoning="low", max_tokens=700)
                    except Exception:  # noqa: BLE001
                        continue
                    al = _extract_al(comp)
                    if not al:
                        continue
                    r = _compile_with(app_dir, rel, member, al, version, sig)
                    pair = G.g7_from_rollout(probe, al, r)
                    if pair:
                        _apply_autofix(pair, al, r, autofix)
                        fh.write(json.dumps(pair) + "\n")
                        n += 1
                        break  # one hard negative per probe is enough
            if limit_probes and probes >= limit_probes:
                break
    print(f"g7 hard negatives: {n} from {probes} probes")
    return n


def _apply_autofix(pair: dict, broken_al: str, compile_result, autofix_fn) -> None:
    """Replace the G7 `chosen` side with a real repair of the model's own output.

    On success the pair carries `chosen = fixed`, `rejected = broken`, and
    `meta.fix_method`; on failure it keeps the gold correction and records why.
    """
    diags = [{"severity": s, "code": c, "message": m}
             for s, c, m in compile_result.diagnostics]
    try:
        fixed, method = autofix_fn(broken_al, diags)
    except Exception as e:  # noqa: BLE001 - a repair failure must not drop the pair
        fixed, method = None, f"error:{e}"
    if fixed and method not in ("already-clean",):
        pair["messages"] = [pair["messages"][0],
                            {"role": "assistant", "content": "```al\n" + fixed + "\n```"}]
        pair["chosen"] = fixed
        pair["rejected"] = broken_al
        pair["meta"] = {**pair["meta"], "fix_method": method, "autofixed": True}
    else:
        pair["chosen"] = pair["target_al"]
        pair["rejected"] = broken_al
        pair["meta"] = {**pair["meta"], "fix_method": method, "autofixed": False}


def _extract_al(text: str) -> str | None:
    import re
    m = re.search(r"```al\s*(.+?)```", text, re.S) or re.search(r"```\s*(.+?)```", text, re.S)
    return m.group(1).strip() if m else None
