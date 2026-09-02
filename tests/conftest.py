"""Shared fixtures: locate the smoke AL project and skip cleanly without a toolchain."""
from __future__ import annotations

import os
import pathlib
import shutil

import pytest

SMOKE_APP = pathlib.Path.home() / "bc-al-data" / ".cache" / "smoke" / "app"
SMOKE_FILE = SMOKE_APP / "src" / "HelloWorld.Codeunit.al"
AL_BIN = pathlib.Path(os.environ.get("AL_BIN", str(pathlib.Path.home() / ".dotnet/tools/al")))


def _needs_toolchain() -> str | None:
    if not AL_BIN.exists():
        return f"AL compiler not found at {AL_BIN} (source env.sh)"
    if not SMOKE_FILE.exists():
        return f"smoke project missing at {SMOKE_APP}"
    if "DOTNET_ROOT" not in os.environ:
        return "DOTNET_ROOT unset (source env.sh)"
    return None


@pytest.fixture(scope="session")
def smoke_app() -> pathlib.Path:
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    return SMOKE_APP


@pytest.fixture(scope="session")
def smoke_file() -> pathlib.Path:
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    return SMOKE_FILE


@pytest.fixture
def smoke_copy(tmp_path) -> pathlib.Path:
    """An isolated copy of the smoke project so a test can write scratch .al
    files without disturbing the shared cache or other tests."""
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    dst = tmp_path / "app"
    shutil.copytree(SMOKE_APP, dst, ignore=shutil.ignore_patterns(".alpackages", "*.app"))
    from bcaldata.verify import _shared_alpackages

    (dst / ".alpackages").symlink_to(_shared_alpackages())
    return dst
