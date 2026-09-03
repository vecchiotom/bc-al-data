# bc-al-data

A data pipeline that mines Microsoft Dynamics 365 **Business Central AL** source
code into a compiler-verified instruction dataset, for fine-tuning a local LLM
that otherwise hallucinates AL syntax.

- **New here?** Read [`GUIDA.md`](GUIDA.md) — a plain-language walkthrough of
  every piece and how it fits together.
- **Technical detail** per stage: [`PIPELINE.md`](PIPELINE.md).
- **Latest working session:** [`MORNING_REPORT.md`](MORNING_REPORT.md).

## Quick start

```sh
source env.sh                 # DOTNET_ROOT, AL_BIN, BC_VERSION, ALCOPS_DIR ...
bin/setup-vendor.sh           # clone BCApps + ALCops, build the ALCops MCP server
uv sync                       # Python deps
uv run pytest -m "not slow"   # 38 passed, 1 skipped
```

## Pipeline

```
uv run bcaldata sources       # 1  clone + pin the AL source repos
uv run bcaldata blocklist     #    build the BC-Bench decontamination list
uv run bcaldata baselines     # 2a compile every app once (which start clean)
uv run bcaldata corpus        # 2b one row per procedure/trigger
uv run bcaldata calibrate-g5  #    map each mutation -> the AL#### code it induces
uv run bcaldata generate      # 3  deterministic generators (G1/G2/G5/G6)
uv run bcaldata generate-g4   #    doc Q&A
uv run bcaldata generate-g8   #    analyzer warning -> clean pairs
uv run bcaldata generate-g3   #    explanations           (needs the local LLM)
uv run bcaldata generate-g7   #    hard negatives         (needs the local LLM)
uv run bcaldata verify --mode inapp   # 4  compile-gate every candidate
uv run bcaldata filter        # 5  dedup + decontaminate + license gate
uv run bcaldata assemble      # 6  -> data/dataset/{train,val,preference,heldout}.jsonl
```

Every generator (`G1`–`G8`) and every term is explained in [`GUIDA.md`](GUIDA.md).

## Requirements

- Node's AL compiler (`al` dotnet global tool, prerelease channel), .NET 10
- BC 28.0 sandbox artifact cached under `~/.bcartifacts.cache` (symbols)
- Python ≥ 3.13, `uv`
- The vendored repos and BC symbol cache are **not** committed — `bin/setup-vendor.sh`
  fetches them.

## Layout

`src/bcaldata/` the pipeline · `data/` inputs and outputs · `tests/` ·
`vendor/` fetched sources (gitignored) · `bin/` setup + the ALCops MCP launcher.
