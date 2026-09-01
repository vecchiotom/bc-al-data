#!/usr/bin/env bash
# Compile one AL project with the full ALCops + Microsoft CodeCop analyzer set.
# Prints diagnostics; exit 0 iff clean (no `error AL`, .app written).
set -uo pipefail
: "${AL_BIN:?source env.sh}"; : "${ALCOPS_DIR:?}"; : "${AL_COMPILER_DIR:?}"
proj="${1:?usage: compile.sh <project-dir> [--no-analyzers]}"
out="$(mktemp -d)/out.app"
azargs=()
if [ "${2:-}" != "--no-analyzers" ]; then
  for d in Common LinterCop PlatformCop FormattingCop ApplicationCop DocumentationCop TestAutomationCop; do
    azargs+=("/analyzer:$ALCOPS_DIR/ALCops.$d.dll")
  done
  azargs+=("/analyzer:$AL_COMPILER_DIR/Microsoft.Dynamics.Nav.CodeCop.dll")
fi
log="$("$AL_BIN" compile "/project:$proj" "/packagecachepath:$proj/.alpackages" "/out:$out" "${azargs[@]}" 2>&1)"
echo "$log" | grep -E ': (error|warning|info) [A-Z]' || true
errs="$(echo "$log" | grep -cE '^\s*error AL[0-9]')"
[ "$errs" -eq 0 ] && [ -f "$out" ] && { echo "COMPILE: clean"; exit 0; } || { echo "COMPILE: FAILED ($errs errors)"; exit 1; }
