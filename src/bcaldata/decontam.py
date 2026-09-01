"""Build the decontamination blocklist from the BC-Bench eval set.

Anything in BC-Bench — file paths, NL prompts, referenced repos/commits — must
never appear in training data or in a generator prompt, or the eval is worthless.
"""
from __future__ import annotations
import json, re
from pathlib import Path

BCBENCH = Path.home() / "BC-Bench" / "dataset"
OUT = Path.home() / "bc-al-data" / "data" / "blocklist.json"


def build() -> dict:
    paths: set[str] = set()
    prompts: list[str] = []
    repos: set[str] = set()
    for jf in BCBENCH.glob("*.jsonl"):
        for line in jf.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            repos.add(d.get("repo", ""))
            for p in d.get("project_paths", []) or []:
                paths.add(p.replace("\\", "/"))
            for key in ("patch", "test_patch"):
                for m in re.finditer(r'^\+\+\+ b/(.+)$', d.get(key, "") or "", re.M):
                    paths.add(m.group(1))
            for key in ("nl_prompt", "description"):
                if d.get(key):
                    prompts.append(d[key].strip())
            for exp in d.get("expected", []) or []:
                if isinstance(exp, dict) and exp.get("text"):
                    prompts.append(exp["text"].strip())
    bl = {
        "repos": sorted(r for r in repos if r),
        "path_fragments": sorted(paths),
        "prompts": sorted(set(prompts)),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(bl, indent=2))
    print(f"blocklist: {len(bl['repos'])} repos, {len(bl['path_fragments'])} path fragments, "
          f"{len(bl['prompts'])} prompts -> {OUT}")
    return bl


def load() -> dict:
    return json.loads(OUT.read_text()) if OUT.exists() else {"repos": [], "path_fragments": [], "prompts": []}


def is_contaminated(path: str, blocklist: dict) -> bool:
    p = path.replace("\\", "/")
    return any(frag and (frag in p or p.endswith(frag)) for frag in blocklist["path_fragments"])
