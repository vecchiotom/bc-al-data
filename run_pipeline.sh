#!/usr/bin/env bash
# Full bc-al-data corpus build. Each stage is resumable; safe to re-run.
# Prereqs: source env.sh ; vLLM up at $LOCAL_LLM_URL for g3/g7.
set -euo pipefail
cd "$(dirname "$0")"
source env.sh

uv run bcaldata sources          # 1  clone + pin BCApps@releases/28.0, ALAppExtensions, devitpro docs
uv run bcaldata blocklist        #    BC-Bench decontamination list
uv run bcaldata baselines        # 2a compile every app  (~1-2h first run, cached)
uv run bcaldata corpus           # 2b member records from the clean apps
uv run bcaldata calibrate-g5     #    mutation -> AL#### code map

uv run bcaldata generate         # 3  g1 g2 g5 g6   (deterministic, minutes)
uv run bcaldata generate-g4      # 3  doc-QA        (deterministic)
uv run bcaldata generate-g3      # 3  explanations  (vLLM, hours)
uv run bcaldata generate-g7      # 3  hard negs     (vLLM + compile, hours)

uv run bcaldata verify           # 4  compile gate over candidates/  (parallel, cached)
uv run bcaldata filter           # 5  dedup + decontam + license
uv run bcaldata assemble         # 6  -> data/dataset/{train,val,preference,heldout}.jsonl + datacard.json
