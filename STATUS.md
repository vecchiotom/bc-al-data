# bc-al-data — environment status

Workspace for the Business Central AL fine-tuning **data pipeline** (see
`deepseek-harness/.agents/notes/proposed/process/2026-09-01-qwen3-8-27b-al-qlora-finetune.md`).
Python env via `uv` (3.13). `source env.sh` before any tool.

## Verified working (2026-09-01)

| Capability | State | How |
|---|---|---|
| AL compiler | ✅ `al` v18.0.40 (`~/.dotnet/tools/al`, needs `DOTNET_ROOT`) | `tools/compile.sh <proj>` |
| BC symbols | ✅ cached, no download: 27.0 / 27.2 / **28.0.46665.54059** (9.3 GB in `~/.bcartifacts.cache/sandbox/`) | `tools/stage_alpackages.sh <proj>` |
| Clean compile against BC 28 BaseApp/System | ✅ | smoke: `.cache/smoke/app` |
| ALCops analyzers (6 cops) | ✅ 123/126 rules; 3 disabled (need `Microsoft.Dynamics.Nav.Analyzers.Common` 18.0.36 — pin later) | DLLs in `$ALCOPS_DIR`, passed via `/analyzer:` |
| Microsoft CodeCop / UICop / AppSourceCop / PTECop | ✅ ship with `al` | `$AL_COMPILER_DIR/Microsoft.Dynamics.Nav.*Cop.dll` |
| AL-LSP | ✅ client `src/bcaldata/alsp.py` (`ALLanguageServer`). **Content-Length framing**; `[AL LSP]` banner + 24-endpoint list on **stderr**. Navigation works (symbols/hover/definition/completion, ~0.3s init). **No diagnostics channel** (no `diagnosticProvider`, no `publishDiagnostics`) — `diagnostics()` delegates to a co-resident AL MCP compiler | `al launchlspserver <proj> --packagecachepath …` |
| AL-MCP | ✅ client `src/bcaldata/mcp_client.py` (`ALMcp`). **Newline-delimited JSON** framing (not Content-Length); 16 tools. Warm `al_compile` ~1s vs ~11s cold → verify `--mode lsp` 10.4x | `al launchmcpserver --transport stdio` |
| ALCops-MCP | ❌ not on nuget.org; `vendor/mcp-server` fails to build (missing Roslyn `Microsoft.CodeAnalysis.*` refs, 93 CS0246). Client `ALCopsMcp` written + tested-when-available; G8 `apply_fix` still blocked | — |
| pwsh + BCContainerHelper | ✅ pwsh 7.6.5 (needs `DOTNET_ROOT`), BcContainerHelper 6.1.16 | `DOTNET_ROOT=~/.dotnet pwsh` |
| GPU training stack | ❌ not installed (local training deferred to cloud — see plan) | — |
| **Corpus pipeline** | ✅ run end-to-end (non-LLM): 75 clean apps → 5 793 members → g1 4 302 / g2 723 / g4 4 054 / g5 2 217 / g6 89 / g8-review 3 301 candidates → in-app compile-gate → filter → `data/dataset/`. G3/G7 pending the GPU. See PIPELINE.md + `datacard.json`. | |
| tree-sitter-al parser | ✅ `src/bcaldata/alparse.py` — 0 parse errors over 19k BCApps members | |
| compile gate | ✅ `src/bcaldata/compile_gate.py` (port of BC-Bench compile-proxy) — real BCApps app compiles clean; G5 mutation → `AL0132`/`AL0111` confirmed | slow per-candidate (see PIPELINE gaps) |
| vLLM G3 paraphrase | ✅ grounded explanation via local Qwen3.8-27B (`reasoning=low`), ~3-6s/call, quality high | |
| BCApps corpus | ✅ `releases/28.0` pinned (matches BC 28.0 symbol cache), MIT | 4519 .al on release branch |

## Data artifacts produced

| File | Rows | Content |
|---|---|---|
| `data/al_compiler_diagnostics.tsv` | 919 | every AL#### code + severity (695 error / 206 warning / 10 info) + enum name, reflected from `Microsoft.Dynamics.Nav.CodeAnalysis.dll` |
| `data/alcops_rules.tsv` | ~126 | ALCops rule ids (AC/DC/FC/LC/PC/TA) + cop + severity + title (parsed from `vendor/Analyzers` source — refine via reflection once the 3 disabled rules are fixed) |

## Layout

```
env.sh                  shared env (source first)
tools/stage_alpackages.sh   populate <proj>/.alpackages from the BC 28 symbol cache
tools/compile.sh            compile <proj> with full ALCops+CodeCop analyzer set; exit 0 iff clean
tools/lsp_smoke.py          AL-LSP client smoke (WIP — framing)
tools/reflect/              dotnet single-file scripts that dumped the diagnostic catalogs
data/                       diagnostic catalogs
vendor/Analyzers            ALCops analyzer source (MIT) — rule catalog + mutation-code reference
vendor/{mcp-server,npm-package}  ALCops MCP + TFM/analyzer-install CLI (MIT)
vendor/alcops-dist/         extracted ALCops.Analyzers 1.1.0 DLLs (net10.0 in use)
.cache/smoke/app            minimal AL project, compiles clean against BC 28
```
