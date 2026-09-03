#!/usr/bin/env bash
# One-time setup on a fresh clone: fetch the vendored repos and build the tools.
set -euo pipefail
cd "$(dirname "$0")/.."
source env.sh
mkdir -p vendor && cd vendor

# BCApps — the AL source corpus, pinned to the branch that matches BC_VERSION
[ -d BCApps ] || git clone --filter=blob:none --depth 1 --branch releases/28.0 \
    https://github.com/microsoft/BCApps
ln -sfn BCApps bcapps

# ALCops analyzers (MIT) — DLLs + MCP server source
for r in Analyzers mcp-server npm-package; do
  [ -d "$r" ] || git clone --depth 1 "https://github.com/ALCops/$r"
done

# extract the prebuilt analyzer DLLs from the release nupkg
mkdir -p alcops-dist && cd alcops-dist
[ -f ALCops.Analyzers.1.1.0.nupkg ] || curl -sL -o ALCops.Analyzers.1.1.0.nupkg \
  https://github.com/ALCops/Analyzers/releases/download/v1.1.0/ALCops.Analyzers.1.1.0.nupkg
[ -d extracted ] || unzip -q -o ALCops.Analyzers.1.1.0.nupkg -d extracted
mkdir -p "$ALCOPS_DIR"
cp -f extracted/lib/net10.0/ALCops.*.dll "$ALCOPS_DIR/"
cp -f "$AL_COMPILER_DIR/Microsoft.Dynamics.Nav.Analyzers.Common.dll" "$ALCOPS_DIR/" 2>/dev/null || true
cd ..

# build the ALCops MCP server (analyze / apply_fix)
cd "$OLDPWD"
bash bin/build-alcops-mcp.sh || echo "WARN: ALCops MCP build failed — G8 apply_fix unavailable"
echo "vendor setup complete."
