"""Shared fixtures: locate the smoke AL project and skip cleanly without a toolchain."""
from __future__ import annotations

import os
import pathlib
import shutil

import pytest

SMOKE_APP = pathlib.Path.home() / "bc-al-data" / ".cache" / "smoke" / "app"
SMOKE_FILE = SMOKE_APP / "src" / "HelloWorld.Codeunit.al"
_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "smoke-app"
AL_BIN = pathlib.Path(os.environ.get("AL_BIN", str(pathlib.Path.home() / ".dotnet/tools/al")))


def _ensure_smoke_app() -> None:
    """Materialize the runtime smoke project from the committed fixture (its
    `.alpackages` is staged from the local BC symbol cache, never committed)."""
    if SMOKE_FILE.exists():
        return
    if not _FIXTURE.exists():
        return
    SMOKE_APP.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_FIXTURE, SMOKE_APP, dirs_exist_ok=True)
    try:
        from bcaldata.verify import _shared_alpackages
        alp = SMOKE_APP / ".alpackages"
        if not alp.exists():
            alp.symlink_to(_shared_alpackages())
    except Exception:  # noqa: BLE001 - symbol cache absent -> compile tests skip anyway
        pass


def _needs_toolchain() -> str | None:
    if not AL_BIN.exists():
        return f"AL compiler not found at {AL_BIN} (source env.sh)"
    _ensure_smoke_app()
    if not SMOKE_FILE.exists():
        return f"smoke fixture missing at {_FIXTURE}"
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
