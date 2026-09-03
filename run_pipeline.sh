#!/usr/bin/env bash
# Full bc-al-data corpus build. Each stage is resumable; safe to re-run.
# Prereqs: bin/setup-vendor.sh done, `source env.sh`, and for g3/g7 a vLLM
# server at $LOCAL_LLM_URL serving $LOCAL_LLM_MODEL.
set -euo pipefail
cd "$(dirname "$0")"
source env.sh

uv run bcaldata sources          # 1  clone + pin BCApps@releases/28.0 + devitpro docs
uv run bcaldata blocklist        #    BC-Bench decontamination list
uv run bcaldata baselines        # 2a compile every BCApps app once  (~40 min, cached)
uv run bcaldata corpus           # 2b member rows from the error-clean apps
uv run bcaldata calibrate-g5     #    mutation -> AL#### code map (sampled)

uv run bcaldata generate         # 3  g1 g2 g5 g6   (deterministic; --g5-per-mutation caps G5)
uv run bcaldata generate-g4      # 3  doc-QA from developer docs (deterministic)
uv run bcaldata generate-g8      # 3  analyzer-review pairs (deterministic)

# --- model-dependent, needs the local LLM; run when the GPU is free ---
uv run bcaldata generate-g3      # 3  grounded explanations   (vLLM)
uv run bcaldata generate-g7      # 3  hard negatives + autofix (vLLM + in-app compile)

uv run bcaldata verify --mode inapp   # 4  compile-gate each candidate inside its origin app
uv run bcaldata filter                # 5  exact + near dedup, decontaminate, license gate
uv run bcaldata assemble              # 6  -> data/dataset/{train,val,preference,heldout}.jsonl + datacard.json
