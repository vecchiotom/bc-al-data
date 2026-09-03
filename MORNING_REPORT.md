# Overnight report — 2026-09-03

> **Superseded by [`RUN_2026-09-04.md`](RUN_2026-09-04.md).** The "Dry-run results"
> and "Known gaps" here are from before the first full run — G2/G6 verify loss,
> the missing sources, and the 6-app baseline were all resolved. Kept for history.

Autonomous session (coordinator + 4 subagents). No GPU used. Everything committed.

## Commits (newest first)

| sha | what |
|---|---|
| `a669cfc` | **verify: in-app compile gate** (`verify_inapp.py`) — the snippet-wrapper verify was fundamentally wrong; g1/g2 `target_al` now the full member |
| `c4e1763` | cli: `generate-g8` + `autofix-eval` commands |
| `f92a7bf` | **G7 auto-fixer** (`autofix.py`) + repair-pair wiring; fixed ALCops MCP `apply_fix` schema |
| `0aa2798` | **G8 per-member analyzer/error attribution** + apply_fix training pairs |
| `f3b03ce` | **G5 mutation catalog** — 14 classic AL error classes + calibration |
| `8f4f73b` | tooling: build ALCops MCP locally |
| `2fa9ff7` | resident AL-LSP + MCP stdio clients |
| `d8909f3` | **complete AL diagnostic map** (1324 codes) |

## What was built

### 1. AL diagnostic map — `data/al_error_map.json` (1324 records)
919 AL#### compiler codes + 405 analyzer rules. 916/919 carry the real compiler
message template (reflected from `Microsoft.Dynamics.Nav.CodeAnalysis.dll`'s
`CompilerDiagnosticsResources`). Each record: severity, category, hallucination
likelihood (116 high / 499 medium), fix strategy, the G5 mutation that induces it,
an example trigger. `data/al_error_map.summary.md` has the ranked top-40.

### 2. Resident tool clients — `alsp.py`, `mcp_client.py`
- **AL LSP** (`al launchlspserver`): Content-Length framing, banner on stderr.
  **Navigation only — it has no diagnostics channel** (verified: no
  `diagnosticProvider`, never sends `publishDiagnostics`). Hover / definition /
  completion / documentSymbol all work.
- **AL MCP** (`al launchmcpserver`): newline-delimited JSON, 16 tools incl.
  `al_compile`, `al_getdiagnostics`. A warm resident `al_compile` is ~10x faster
  than a cold one.
- **ALCops MCP**: was blocked (not on nuget, `vendor/mcp-server` wouldn't build).
  Fixed — `bin/build-alcops-mcp.sh` symlinks the BC DevTools DLLs from the `al`
  tool store; `bin/alcops-mcp` runs. 5 tools: `analyze` (structured JSON diags
  with `hasCodeFix`), `list_rules`, `get_fixes`, `apply_fix`, `apply_fix_all`.
  **39 of 113 ALCops rules carry a code fix; the rest are advisory.**

### 3. G5 mutation catalog — `src/bcaldata/mutations.py` (14 mutations)
`m_delete_semicolon` (AL0111), `m_rename_call` / `m_rename_member` (AL0132),
`m_rename_identifier` / `m_remove_var_decl` (AL0118), `m_rename_type` (AL0134/85),
`m_rename_trigger` (AL0162), `m_swap_argument_count` (AL0126),
`m_add_parens_to_property` (AL0125/27), `m_semicolon_before_else` (AL0110),
`m_delete_begin` / `m_delete_then` (AL0104/09), `m_keyword_as_identifier` (AL0105),
`m_change_var_type` (AL0122). Calibration (`data/g5_calibration.md`) on 1015
compiles: 12/14 land on an expected code; the 2 noisy ones still yield valid
broken samples (verify drops the misfires, so keeping them is free).

### 4. G7 auto-fixer — `src/bcaldata/autofix.py`
`autofix(broken_al, diagnostics) -> (fixed_al | None, method)`, tried in order:
structural/deterministic (missing `;`, orphaned else, bad `using`, keyword clash) →
near-name repair (Levenshtein ≤ 2 vs sibling names + LSP completions + corpus
vocab — undoes invented `FooX` / misspelled `Fooo`) → ALCops `apply_fix` for
analyzer warnings → unfixable. Wired into `run_g7`: a non-compiling model
completion becomes a preference pair `chosen = auto-fixed`, `rejected = broken`
(falls back to gold when unfixable).

### 5. Per-member attribution + G8 — `build_corpus.py`, `generate_g8.py`
Every compiler diagnostic (`file(line,col): sev CODE`) is mapped to the corpus
member whose byte range contains that line → `error_hits` / `analyzer_hits` per
member. G8 turns members with analyzer hits into `(as-written → analyzer-clean)`
pairs via ALCops `apply_fix`, plus a deterministic review variant.

### 6. verify — corrected to in-app compilation (`src/bcaldata/verify_inapp.py`)
**The original snippet-wrapper verify was wrong**: a procedure extracted from its
object references sibling globals / `Rec` that don't resolve in a bare wrapper,
so even verbatim BCApps code failed to "compile". `verify_inapp` drops the
candidate back into a worktree copy of its real app and compiles the whole app
(BC-Bench compile-proxy approach). Fast path: a candidate that is the verbatim
original and whose app baselines clean is kept without a recompile.
`bcaldata verify --mode inapp`.

## Dry-run results (non-LLM, capped sample, in-app verify)

| generator | verified | rate | note |
|---|---|---|---|
| **G1 FIM** | 20/20 | **100%** | after `target_al = member_text` fix |
| G2 intent→impl | 12/20 | 60% | failures dropped; ~30-40% need investigation (doc-comment/whitespace mismatch in the verbatim check) |
| **G5 error→fix** | 1171 (partial, stopped for the server) | ~96% on the finished cell | codes induced: **AL0104** (syntax) 314, **AL0118** (undeclared/invented name) 244, **AL0132** (invented method/member) 189, AL0107 139, AL0111 (`;`) 112, **AL0126** (arg count) 72, **AL0162** (invented trigger)… — exactly the "hallucinated syntax" classes |
| G6 spec→object | not finished | | fast path added (verbatim-in-baseline-clean-app) + fresh-app fallback with id remap |
| G8 review | 8/8 | 100% | text target, no compile |

## Known gaps / next steps

1. **`bcaldata sources`** — only BCApps (`releases/28.0`) is cloned. Run it to add
   `microsoft/ALAppExtensions` + the devitpro docs repo (G4 = 0 without docs).
2. **Full `bcaldata baselines`** — only 6 apps baselined for the dry run. The full
   run compiles every BCApps app once (~1-2h, resumable, cached).
3. **verify throughput** — g1/g2/g6 verbatim use the instant baseline fast path;
   g5/g7 need one `al compile` each (~15-45s). For a large corpus, batch g5
   candidates by app (compile once per app-with-all-its-mutations) — not yet done.
4. **G2/G6 ~35% verify loss** — the verbatim-match normalization is too strict
   (attributes, doc-comment inclusion). Loosen `_norm` / compare member bodies.
5. **G8 apply_fix** covers only the ~39 fixable ALCops rules and depends on
   default rule enablement; the review variant carries the rest.
6. **`corpus.jsonl` was rebuilt** with correct repo-relative paths mid-session —
   an earlier ad-hoc build used the module folder as root. `build_corpus` is
   correct; re-run it for the real corpus.
7. autofix repair rate on the G5 broken set was low (1/120) because that eval
   compiled the mutated member in isolation (same wrapper bug) — re-run
   `autofix-eval` now that verify is in-app, and expect near-name repair to do
   better on real model output (which has surrounding context).

## Test status
`uv run pytest -m "not slow"`: **38 passed, 1 skipped** (ALCops `apply_fix` on
DC0007 — advisory rule, no working fix). Slow tests (compile-touching) not run in
this summary.
