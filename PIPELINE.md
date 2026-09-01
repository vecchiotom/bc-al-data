# bc-al-data — corpus pipeline

`./run_pipeline.sh` (or `uv run bcaldata <stage>`). Every stage is resumable and
content-addressed; re-running only redoes changed inputs.

| Stage | cmd | in | out | model? | ~cost |
|---|---|---|---|---|---|
| 1 source | `sources` | — | `vendor/{bcapps,alappextensions,devitpro}`, `data/sources.lock.json` | no | mins |
| 1 blocklist | `blocklist` | `~/BC-Bench/dataset/*.jsonl` | `data/blocklist.json` | no | secs |
| 2a baseline | `baselines` | source apps | `data/app_baseline.json` (clean set + analyzer profile) | no | 1–2 h (cached) |
| 2b corpus | `corpus` | clean apps | `data/corpus.jsonl` (1 row/member) | no | mins |
| — calib | `calibrate-g5` | corpus | `data/g5_calibration.json` (mutation→`AL####`) | no | ~10 min |
| 3 | `generate` | corpus | `data/candidates/{g1_fim,g2_sig2body,g5_error_fix,g6_spec2object}.jsonl` | no | mins |
| 3 | `generate-g4` | devitpro md | `data/candidates/g4_docqa.jsonl` | no | mins |
| 3 | `generate-g3` | corpus | `data/candidates/g3_explain.jsonl` (grounded paraphrase) | **vLLM** | hours |
| 3 | `generate-g7` | corpus | `data/candidates/g7_hard_negative.jsonl` | **vLLM + compile** | hours |
| 4 verify | `verify` | candidates/ | `data/verified/*.jsonl` (compile-gated) | no | parallel, cached |
| 5 filter | `filter` | verified/ | `data/filtered/*.jsonl` (dedup + decontam + license) | no | mins |
| 6 assemble | `assemble` | filtered/ | `data/dataset/{train,val,preference,heldout}.jsonl`, `datacard.json` | no | secs |

## Generators

| id | task | signal | source |
|---|---|---|---|
| G1 | fill-in-the-middle procedure body | SFT | real AL, compile-verified |
| G2 | doc-comment intent → implementation | SFT | real AL w/ doc-comment |
| G3 | explain / review a procedure | SFT | deterministic facts (call list, record types, return) **grounded**, prose by vLLM |
| G4 | BC-AL doc Q&A | SFT | devitpro markdown H2/H3 sections |
| G5 | broken AL → fixed AL | preference (chosen/rejected) | clean member + one tree-sitter mutation; kept only if it breaks compile with the calibrated code |
| G6 | NL spec → object | SFT | small self-contained enum/table |
| G7 | hallucinated AL → compiled AL | preference | current model's own non-compiling completions on real prompts, classified METHOD/PARAMETER/OBJECT/TRIGGER |
| G8 | analyzer warning → clean AL | SFT + preference / review | members with ALCops/CodeCop hits (from Stage 2a); fix via ALCops MCP `apply_fix` |

## Determinism & hygiene guarantees

- **Corpus selection is `sha1(path) % N`** — never a ranked/model choice.
- **Every AL target is compiled** against the pinned BC 28.0 symbol cache with the
  full ALCops + CodeCop analyzer set (Stage 4). Non-compiling positives are dropped.
- **Decontamination**: any file path / NL prompt / repo+commit present in
  `~/BC-Bench/dataset/*.jsonl` is excluded (Stage 5).
- **Held-out by whole app** (`sha1(app) % 12`) — reserved apps never enter
  train/val or any generator prompt.
- **License gate**: only SPDX ∈ {MIT, Apache-2.0, MS-PL, BSD, ISC} (docs: CC-BY).
- **Provenance** (repo, path, commit, license) travels on every row to the datacard.

## Known gaps (before a production run)

- BCApps `releases/28.0` shallow checkout: some System Application sub-apps don't
  baseline-compile solo (unshipped inter-app dep versions) → skipped, not fixed.
- G8 `apply_fix` wiring to the ALCops MCP stdio client is stubbed (`generators.g8_*`
  emits the review-only variant until the client lands).
- `tools/alsp.py` (LSP client for precise hover/definition signatures) not written;
  `build_corpus` uses tree-sitter only. Retrieval index for inference-time not built.
- G7 rollout throughput depends on vLLM; batch it on the training GPU, not locally.
