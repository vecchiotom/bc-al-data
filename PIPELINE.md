# bc-al-data — corpus pipeline

`./run_pipeline.sh` (or `uv run bcaldata <stage>`). Every stage is resumable and
content-addressed; re-running only redoes changed inputs.

| Stage | cmd | in | out | model? | ~cost |
|---|---|---|---|---|---|
| 1 source | `sources` | — | `vendor/{bcapps,alappextensions,devitpro}`, `data/sources.lock.json` | no | mins |
| 1 blocklist | `blocklist` | `~/BC-Bench/dataset/*.jsonl` | `data/blocklist.json` | no | secs |
| 2a baseline | `baselines` | source apps | `data/app_baseline.json` (clean set + analyzer profile) | no | 1–2 h (cached) |
| 2b corpus | `corpus` | clean apps | `data/corpus.jsonl` (1 row/member) | no | mins |
| — calib | `calibrate-g5` | corpus | `data/g5_calibration.json` + `data/g5_calibration.md` (per-mutation: applicability %, any-new-error %, modal new `AL####`, matches-expected) | no | ~1–2 h (cold `al compile` per sample × mutation) |
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
| G4 | BC-AL doc Q&A | SFT | devitpro `dev-itpro/developer/` pages: one pair per method/property/trigger/type reference page, plus concept H2/H3 sections that pass the prose and heading filters |
| G5 | broken AL → fixed AL | preference (chosen/rejected) | clean member + one localized mutation from the 14-entry `mutations.py` catalog (tree-sitter-al node replacement); kept only if the broken side fails to compile and the clean side does not |
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
- G8 `apply_fix` wiring: the ALCops MCP stdio client exists
  (`mcp_client.ALCopsMcp.apply_fix`), but the `alcops-mcp` server is not
  runnable here — it is not on nuget.org and `vendor/mcp-server` fails to build
  against the shipped BC DevTools (Roslyn `Microsoft.CodeAnalysis.*` reference
  assemblies missing at build time, 93 `CS0246`). `generators.g8_*` still emits
  the review-only variant. `ALCopsMcp` is tested only when a build appears
  (`alcops_mcp_command()`); TODO: obtain an `alcops-mcp` build or vendor the
  missing Roslyn refs.
- **AL-LSP client** (`src/bcaldata/alsp.py`) — written. `al launchlspserver`
  uses **`Content-Length` framing**; the `[AL LSP]` banner and 24-endpoint list
  print to **stderr** (not stdout). Navigation works and is fast (~0.3 s init,
  warm thereafter): `document_symbols`, `hover`, `definition`, `completion`.
  **The agentic AL LSP has no diagnostics channel** — no `diagnosticProvider`
  capability, no `textDocument/publishDiagnostics`, and `textDocument/diagnostic`
  / `workspace/diagnostic` are unanswered (probed with real errors, `didSave`,
  `didChange`). `ALLanguageServer.diagnostics()` therefore delegates to a
  co-resident AL MCP compiler.
- **AL-MCP client** (`src/bcaldata/mcp_client.py`) — written. `al launchmcpserver
  --transport stdio` uses **newline-delimited JSON** (not `Content-Length`); 16
  tools (`al_compile`, `al_getdiagnostics`, `al_build`, `al_run_tests`,
  `al_addproject`, `al_symbolsearch`, …).
- `build_corpus` still uses tree-sitter only; a retrieval index for
  inference-time is not built.
- G7 rollout throughput depends on vLLM; batch it on the training GPU, not locally.
- **Verify throughput**: a cold `al compile` is ~11 s here (measured; ~15-45 s on
  a cold host) — process start + JIT + 350-package symbol load + 7 analyzer DLLs
  per candidate. Mitigations:
  1. **wired** — `verify.py` `mode="lsp"` (`uv run bcaldata verify --mode lsp`,
     also `verify_batch_via_lsp`): one resident AL server per worker, warm
     `al_compile` per g1/g2/g6 candidate. Measured **10.4x** (1.04 s vs 10.9 s
     over 10 snippets). g5/g7 and text targets stay on the cold `al compile` (a
     real `/out` artifact + exact error class). Default is still `mode="compile"`.
  2. or batch candidates into a few multi-file projects, compile once, map
     diagnostics back by file;
  3. Stage-4 cache (content-hash, already implemented) makes re-runs free.
