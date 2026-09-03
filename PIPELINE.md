# bc-al-data — corpus pipeline

`./run_pipeline.sh` (or `uv run bcaldata <stage>`). Every stage is resumable and
content-addressed; re-running only redoes changed inputs.

| Stage | cmd | in | out | model? | ~cost |
|---|---|---|---|---|---|
| 1 source | `sources` | — | `vendor/{bcapps,devitpro}`, `data/sources.lock.json` | no | mins |
| 1 blocklist | `blocklist` | `~/BC-Bench/dataset/*.jsonl` | `data/blocklist.json` | no | secs |
| 2a baseline | `baselines` | source apps | `data/app_baseline.json` (clean set + per-file diagnostics) | no | ~40 min (cached) |
| 2b corpus | `corpus` | clean apps | `data/corpus.jsonl` (1 row/member, w/ `error_hits`/`analyzer_hits`) | no | mins |
| — calib | `calibrate-g5` | corpus | `data/g5_calibration.json` + `.md` (per-mutation: applicability %, any-new-error %, modal new `AL####`) | no | ~20 min (sampled) |
| 3 | `generate` | corpus | `candidates/{g1_fim,g2_sig2body,g5_error_fix,g6_spec2object}.jsonl` — G5 capped `--g5-per-{mutation,file,app}` | no | secs |
| 3 | `generate-g4` | devitpro md | `candidates/g4_docqa.jsonl` | no | mins |
| 3 | `generate-g8` | corpus | `candidates/{g8_review,g8_warning_clean}.jsonl` | no | mins |
| 3 | `generate-g3` | corpus | `candidates/g3_explain.jsonl` (grounded paraphrase) | **vLLM** | hours |
| 3 | `generate-g7` | corpus | `candidates/g7_hard_negative.jsonl` (+ autofix) | **vLLM + compile** | hours |
| 4 verify | `verify --mode inapp` | candidates/ | `data/verified/*.jsonl` | no | g1/g2/g6 instant (baseline), g5/g7 ~15-25 s/compile, parallel + cached |
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
| G8 | analyzer finding → review (+ clean-AL pair when a fix exists) | SFT / preference | members with ALCops/CodeCop hits attributed at Stage 2a; `apply_fix` via the ALCops MCP when the rule carries one (currently none in-corpus → review-only) |

## Determinism & hygiene guarantees

- **Corpus selection is `sha1(path) % N`** — never a ranked/model choice.
- **Every AL target is compiled inside its origin app** (Stage 4, `--mode inapp`):
  the candidate text is dropped back into a hardlink worktree of its real BCApps
  app at the member's tree-sitter byte range and the whole app is compiled against
  the pinned BC 28.0 symbols. A member yanked into a bare wrapper references
  siblings/`Rec` that don't resolve, so the old snippet path failed even verbatim
  source. Positives (g1/g2/g6): app must stay error-clean — when the candidate is
  the verbatim original of a baseline-clean app that is asserted with no recompile.
  g5/g7: app must be clean at baseline and NOT compile with `rejected_al` in place.
- **Decontamination**: any file path / NL prompt / repo+commit present in
  `~/BC-Bench/dataset/*.jsonl` is excluded (Stage 5).
- **Held-out by whole app** (`sha1(app) % 12`) — reserved apps never enter
  train/val or any generator prompt.
- **License gate**: only SPDX ∈ {MIT, Apache-2.0, MS-PL, BSD, ISC} (docs: CC-BY).
- **Provenance** (repo, path, commit, license) travels on every row to the datacard.

## Known gaps

- **Corpus base = 75 error-clean BCApps apps** (~5.8 k members). The other ~248
  apps don't compile solo: `System Application/App/DotNet Aliases` fails
  `AL0452` (a .NET Framework reference assembly, `System.ServiceModel.Primitives`,
  is absent from the artifact — a Windows-BC-dev-box dependency), and everything
  that transitively needs the full System Application cascades. A topological
  build against source-built sibling symbols was tried and gained only +7 apps,
  so it was reverted. The clean 75 skew toward product App code (System
  Application core modules, Business Foundation, most `Apps/W1/*/App`) — the right
  material for teaching AL — and exclude most test apps and dotnet-interop.
- **G8 `apply_fix`** produces nothing: the ALCops MCP server builds and runs
  (`bin/alcops-mcp`), but none of the analyzer rules actually hit in the corpus
  (`PC0037`, `AC0031`, `FC0003`, `DC0004`, …) carry a working code fix through it
  — `rules_with_working_apply_fix: []`. Only `g8_review` (name the findings, no
  fix) is emitted. A per-rule deterministic fixer for the formatting cops
  (`FC000x`, ~1 k hits, trivially fixable) is the obvious next add.
- **AL-LSP has no diagnostics channel** (`alsp.py`) — no `diagnosticProvider`, no
  `publishDiagnostics`; navigation (`hover`/`definition`/`completion`/
  `documentSymbol`) works. Verify does not use it; `mode="lsp"` in `verify.py` is
  dead and kept only for the resident-`al_compile` experiment.
- **AL-MCP** (`mcp_client.py`, `al launchmcpserver --transport stdio`,
  newline-delimited JSON, 16 tools) — used by `autofix` for completion lookups,
  not on the verify hot path.
- **G3 / G7 need the local vLLM** and are fenced off in `run_pipeline.sh`; run
  them when the GPU is free. `generate-g7` compiles each rollout in-app and
  auto-fixes it (`autofix.py`).
- No inference-time retrieval index is built.
