"""Stage 1 — deterministic source acquisition.

Every repo is pinned to an explicit ref, shallow + blob-filtered, license-gated.
`sources.lock.json` records exactly what was checked out.
"""
from __future__ import annotations
import json, subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

VENDOR = Path.home() / "bc-al-data" / "vendor"
LOCK = Path.home() / "bc-al-data" / "data" / "sources.lock.json"

ALLOWED_SPDX = {"MIT", "Apache-2.0", "MS-PL", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "ISC"}


@dataclass(frozen=True)
class Source:
    key: str
    url: str
    ref: str                 # branch or tag — pinned, matches the BC symbol version
    spdx: str
    role: str                # "mine" (extract AL) | "docs" (markdown QA) | "reference"
    subdir: str = "src"      # where the .al / .md live


SOURCES: list[Source] = [
    Source("bcapps", "https://github.com/microsoft/BCApps", "releases/28.0", "MIT", "mine", "src"),
    # ALAppExtensions ships no `releases/28.0` branch and its `main` tracks the next
    # platform (29.x), so every app there mismatches the cached BC 28.0 symbols and
    # baselines dirty. Excluded until a version-matched ref exists.
    Source("devitpro", "https://github.com/MicrosoftDocs/dynamics365smb-devitpro-pb", "main", "CC-BY-4.0", "docs", "dev-itpro"),
    # community ISV apps are added here after a manual license check → SPDX in ALLOWED_SPDX
]


def _run(*a: str, cwd: Path | None = None) -> str:
    return subprocess.run(a, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fetch(src: Source, *, force: bool = False) -> dict:
    dest = VENDOR / src.key
    if dest.exists() and not force:
        head = _run("git", "-C", str(dest), "rev-parse", "HEAD")
    else:
        if dest.exists():
            _run("rm", "-rf", str(dest))
        _run("git", "clone", "--filter=blob:none", "--depth", "1", "--branch", src.ref, src.url, str(dest))
        head = _run("git", "-C", str(dest), "rev-parse", "HEAD")
    n_al = sum(1 for _ in (dest / src.subdir).rglob("*.al")) if src.role == "mine" else 0
    n_md = sum(1 for _ in (dest / src.subdir).rglob("*.md")) if src.role == "docs" else 0
    return {**asdict(src), "commit": head, "n_al": n_al, "n_md": n_md}


def fetch_all(*, force: bool = False) -> None:
    for s in SOURCES:
        assert s.spdx in ALLOWED_SPDX or s.role == "docs", f"license {s.spdx} not allowed for {s.key}"
    lock = []
    for s in SOURCES:
        try:
            lock.append(fetch(s, force=force))
        except subprocess.CalledProcessError as e:  # network / missing ref — record and continue
            lock.append({**asdict(s), "commit": None, "n_al": 0, "n_md": 0,
                         "error": (e.stderr or str(e)).strip()[:300]})
    LOCK.parent.mkdir(exist_ok=True)
    LOCK.write_text(json.dumps(lock, indent=2))
    for row in lock:
        status = row.get("error") or f"{(row['commit'] or '')[:12]}  al={row['n_al']} md={row['n_md']}"
        print(f"  {row['key']:16} {row['ref']:16} {status}")
