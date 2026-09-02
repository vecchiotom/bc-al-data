#!/usr/bin/env bash
# Build the ALCops MCP server locally (not on nuget.org; vendor/mcp-server needs
# the BC DevTools DLLs, which ship inside the `al` dotnet tool store).
set -euo pipefail
source "$(dirname "$0")/../env.sh"
STORE="$AL_COMPILER_DIR"                 # .../tools/net10.0/any
STORE8="${STORE/net10.0/net8.0}"
BCDT="$HOME/bc-al-data/vendor/Microsoft.Dynamics.BusinessCentral.Development.Tools"
mkdir -p "$BCDT/net8.0" "$BCDT/net10.0"
ln -sf "$STORE8"/*.dll  "$BCDT/net8.0/"
ln -sf "$STORE"/*.dll   "$BCDT/net10.0/"
cd "$HOME/bc-al-data/vendor/mcp-server"
DOTNET_ROOT="$HOME/.dotnet" "$HOME/.dotnet/dotnet" build src/ALCops.Mcp/ALCops.Mcp.csproj -c Release -p:BcDevToolsDir="$BCDT" -v q
OUT="src/ALCops.Mcp/bin/Release/net10.0"
for f in Microsoft.Dynamics.Nav.CodeAnalysis Microsoft.Dynamics.Nav.CodeAnalysis.Workspaces \
         Microsoft.Dynamics.Nav.Analyzers.Common Microsoft.CodeAnalysis Microsoft.CodeAnalysis.CSharp; do
  cp -Lf "$BCDT/net10.0/$f.dll" "$OUT/" 2>/dev/null || true
done
echo "built: $HOME/bc-al-data/vendor/mcp-server/$OUT/ALCops.Mcp.dll"
echo "launcher: $HOME/bc-al-data/bin/alcops-mcp  (5 tools: analyze, list_rules, get_fixes, apply_fix, apply_fix_all)"
