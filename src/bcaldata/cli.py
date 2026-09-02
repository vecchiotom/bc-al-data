"""bc-al-data pipeline CLI.  Run stages in order; each is resumable.

  uv run bcaldata sources          # Stage 1: clone + pin source repos
  uv run bcaldata blocklist        # build BC-Bench decontamination blocklist
  uv run bcaldata baselines        # Stage 2a: compile every app, record clean set
  uv run bcaldata corpus           # Stage 2b: member records from clean apps
  uv run bcaldata calibrate-g5     # map G5 mutations -> AL#### codes
  uv run bcaldata generate         # Stage 3: deterministic generators
  uv run bcaldata generate-g3      # Stage 3: model-paraphrased explanations
  uv run bcaldata generate-g4      # Stage 3: doc-QA
  uv run bcaldata generate-g7      # Stage 3: model hard-negative rollouts
  uv run bcaldata verify           # Stage 4: compile gate over candidates/
  uv run bcaldata filter           # Stage 5: dedup + decontam + license
  uv run bcaldata assemble         # Stage 6: splits + ShareGPT + datacard
"""
from __future__ import annotations
from pathlib import Path
import typer

app = typer.Typer(add_completion=False, help=__doc__)
DATA = Path.home() / "bc-al-data" / "data"


@app.command()
def sources(force: bool = False):
    from .sources import fetch_all
    fetch_all(force=force)


@app.command()
def blocklist():
    from .decontam import build
    build()


@app.command()
def baselines(workers: int = 0):
    from .build_corpus import build_baselines
    import os
    build_baselines(workers or max(1, os.cpu_count() // 2))


@app.command()
def corpus(all_apps: bool = False):
    from .build_corpus import build_members
    build_members(only_clean_apps=not all_apps)


@app.command("calibrate-g5")
def calibrate_g5(n: int = 120):
    from .calibrate_g5 import calibrate
    calibrate(n)


@app.command()
def generate(limit_per_gen: int = 0):
    from .generate import run_deterministic
    run_deterministic(limit_per_gen or None)


@app.command("generate-g3")
def generate_g3(limit: int = 0):
    from .generate import run_g3
    run_g3(limit or None)


@app.command("generate-g4")
def generate_g4():
    from .generate import run_g4
    run_g4()


@app.command("generate-g7")
def generate_g7(k: int = 8, limit_probes: int = 400):
    from .generate import run_g7
    run_g7(k, limit_probes)


@app.command()
def verify(workers: int = 0, mode: str = "compile"):
    """mode=compile (authoritative) or mode=lsp (g1/g2/g6 via resident AL-LSP, ~50x faster)."""
    import os
    from .verify import verify_file
    cand, out = DATA / "candidates", DATA / "verified"
    out.mkdir(exist_ok=True)
    for jf in sorted(cand.glob("*.jsonl")):
        verify_file(jf, out / jf.name, workers or max(1, os.cpu_count() // 2), mode=mode)


@app.command()
def filter():
    from .filter import filter_file
    vin, out = DATA / "verified", DATA / "filtered"
    out.mkdir(exist_ok=True)
    for jf in sorted(vin.glob("*.jsonl")):
        filter_file(jf, out / jf.name)


@app.command()
def assemble():
    from .assemble import assemble as _a
    _a(DATA / "filtered")


if __name__ == "__main__":
    app()
