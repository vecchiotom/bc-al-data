#!/usr/bin/env bash
# Populate an AL project's .alpackages with the BC symbol set for $BC_VERSION.
set -euo pipefail
: "${BC_ARTIFACT:?source env.sh}"
proj="${1:?usage: stage_alpackages.sh <project-dir>}"
mkdir -p "$proj/.alpackages"
ln -sf "$BC_ARTIFACT"/w1/Extensions/Microsoft_*.app "$proj/.alpackages/"
sys="$BC_ARTIFACT/platform/ModernDev/PFiles/Microsoft Dynamics NAV/280/AL Development Environment/System.app"
[ -f "$sys" ] && ln -sf "$sys" "$proj/.alpackages/"
echo "staged $(ls "$proj/.alpackages" | wc -l) symbol packages"
