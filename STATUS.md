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
| AL-LSP | ⚠️ server starts, 24 endpoints (`documentSymbol`, `hover`, `definition`, `completion`, `publishDiagnostics`); stdio client uses **Content-Length framing** — client not yet written | `al launchlspserver <proj> --packagecachepath …` |
| AL-MCP | ⚠️ server runs; also live in the dsh harness (`al-mcp`, 16 tools, `mcp-status` = connected). stdio client TBD | `al launchmcpserver --transport stdio` |
| pwsh + BCContainerHelper | ✅ pwsh 7.6.5 (needs `DOTNET_ROOT`), BcContainerHelper 6.1.16 | `DOTNET_ROOT=~/.dotnet pwsh` |
| GPU training stack | ❌ not installed (local training deferred to cloud — see plan) | — |

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
