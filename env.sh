# source this: shared env for the bc-al-data pipeline
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
export AL_BIN="$HOME/.dotnet/tools/al"
export BC_VERSION="28.0.46665.54059"          # matches served qwen3.8-27b env; symbols cached
export BC_ARTIFACT="$HOME/.bcartifacts.cache/sandbox/$BC_VERSION"
export AL_COMPILER_DIR="$HOME/.dotnet/tools/.store/microsoft.dynamics.businesscentral.development.tools/18.0.40.43394-beta/microsoft.dynamics.businesscentral.development.tools/18.0.40.43394-beta/tools/net10.0/any"
export ALCOPS_DIR="$AL_COMPILER_DIR/Analyzers"
