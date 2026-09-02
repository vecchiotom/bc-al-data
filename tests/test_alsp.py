"""Resident AL language server client — diagnostics, symbols, hover.

Skips without the AL toolchain (`source env.sh`). One `ALLanguageServer` is
shared across the module over an isolated copy of the smoke project, so tests
may write scratch `.al` files without touching the shared cache.

The agentic AL LSP has no diagnostics channel, so `diagnostics()` delegates to a
co-resident AL MCP compiler (see `bcaldata.alsp` docstring); the error-clean
checks below exercise that path.
"""
from __future__ import annotations

import shutil

import pytest

from bcaldata.alsp import ALLanguageServer
from conftest import SMOKE_APP, _needs_toolchain

pytestmark = pytest.mark.timeout(900)


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    dst = tmp_path_factory.mktemp("alsp") / "app"
    shutil.copytree(SMOKE_APP, dst, ignore=shutil.ignore_patterns(".alpackages", "*.app"))
    from bcaldata.verify import _shared_alpackages

    (dst / ".alpackages").symlink_to(_shared_alpackages())
    return dst


@pytest.fixture(scope="module")
def server(project):
    srv = ALLanguageServer(project, timeout=300).start()
    yield srv
    srv.close()


@pytest.fixture(scope="module")
def main_file(project):
    return project / "src" / "HelloWorld.Codeunit.al"


def test_diagnostics_flag_a_semantic_error(server, project):
    f = project / "src" / "ScratchErr.al"
    bad = ('codeunit 50077 "Scratch Err"\n{\n  procedure P(): Integer\n  begin\n'
           '    exit(DoesNotExist + 1);\n  end;\n}\n')
    try:
        diags = server.diagnostics(f, bad)
        errs = [d for d in diags if d["severity"] == 1]
        assert errs, diags
        assert any(c.startswith("AL") for c in (d["code"] for d in errs))
        for d in diags:
            assert d["severity"] in (1, 2, 3, 4)
            assert "range" in d
    finally:
        f.unlink(missing_ok=True)


def test_error_clean_roundtrip(server, project):
    f = project / "src" / "ScratchClean.al"
    good = ('codeunit 50078 "Scratch Clean"\n{\n  procedure Add(A: Integer; B: Integer): Integer\n'
            '  begin\n    exit(A + B);\n  end;\n}\n')
    assert server.is_error_clean(f, good) is True
    assert server.is_error_clean(f, good.replace("A + B", "A + Nope")) is False


def test_document_symbols_find_codeunit_and_member(server, main_file):
    syms = server.document_symbols(main_file, main_file.read_text())
    assert syms
    names: list[str] = []

    def walk(node: dict) -> None:
        names.append(node.get("name", ""))
        for c in node.get("children", []) or []:
            walk(c)

    for s in syms:
        walk(s)
    assert any("Hello World" in n for n in names), names
    assert any("OnRun" in n for n in names), names


def test_hover_returns_text(server, main_file):
    text = main_file.read_text()
    server.open_document(main_file, text)
    lines = text.splitlines()
    line = next(i for i, ln in enumerate(lines) if "Record Customer" in ln)
    col = lines[line].index("Customer")
    assert isinstance(server.hover(main_file, line, col), str)
