"""AL MCP and ALCops MCP stdio clients.

AL MCP is exercised against an isolated copy of the smoke project. ALCops MCP is
skipped unless the `alcops-mcp` global tool is installed or `vendor/mcp-server`
has been built (it currently fails to build against the shipped BC DevTools —
see PIPELINE.md "Known gaps").
"""
from __future__ import annotations

import shutil

import pytest

from bcaldata.mcp_client import ALCopsMcp, ALMcp, alcops_mcp_command
from conftest import SMOKE_APP, _needs_toolchain

pytestmark = pytest.mark.timeout(900)


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    dst = tmp_path_factory.mktemp("almcp") / "app"
    shutil.copytree(SMOKE_APP, dst, ignore=shutil.ignore_patterns(".alpackages", "*.app"))
    from bcaldata.verify import _shared_alpackages

    (dst / ".alpackages").symlink_to(_shared_alpackages())
    return dst


@pytest.fixture(scope="module")
def al_mcp(project):
    al = ALMcp(projects=[project], timeout=300).start()
    yield al
    al.close()


def test_al_mcp_uses_newline_framing_and_lists_tools(al_mcp):
    assert al_mcp.mcp._framing == "line"
    names = al_mcp.tool_names()
    assert "al_compile" in names
    assert "al_getdiagnostics" in names
    assert al_mcp.mcp.server_info.get("name")


def test_al_mcp_compile_smoke_is_error_clean(al_mcp, project):
    res = al_mcp.compile(project, enable_code_analysis=True, only_errors=False)
    assert isinstance(res, dict)
    assert res.get("succeeded") is True, res
    errs = [d for d in res.get("diagnostics", [])
            if str(d.get("severity", "")).lower() == "error"]
    assert not errs, errs


def test_al_mcp_compile_reports_error_on_bad_al(al_mcp, project):
    bad = project / "src" / "PytestBad.al"
    bad.write_text('codeunit 50090 "Pytest Bad"\n{\n  procedure P(): Integer\n  begin\n'
                   '    exit(Nope + 1);\n  end;\n}\n')
    try:
        res = al_mcp.compile(project, only_errors=True)
        assert res.get("succeeded") is False
        codes = {str(d.get("code") or d.get("id")) for d in res.get("diagnostics", [])}
        assert any(c.startswith("AL") for c in codes), codes
    finally:
        bad.unlink(missing_ok=True)


def test_al_mcp_getdiagnostics_scopes(al_mcp, project):
    res = al_mcp.get_diagnostics(project_path=project, severities=["Error"])
    assert isinstance(res, dict)
    assert res.get("succeeded") is True


@pytest.mark.skipif(alcops_mcp_command() is None,
                    reason="alcops-mcp not installed and vendor/mcp-server not built")
def test_alcops_list_rules_and_apply_fix(project):
    with ALCopsMcp(timeout=300) as ac:
        rules = ac.list_rules()
        assert len(rules) > 100
        target = project / "src" / "HelloWorld.Codeunit.al"
        diags = ac.analyze(project=project)
        hit = _first_fixable(diags)
        if hit is None:
            pytest.skip("no fixable analyzer hit in smoke project")
        before = target.read_text()
        after = ac.apply_fix(target, hit)
        assert after != before


def _first_fixable(diags: object) -> dict | None:
    items = diags.get("diagnostics", []) if isinstance(diags, dict) else diags
    if not isinstance(items, list):
        return None
    for d in items:
        if isinstance(d, dict) and (d.get("hasFix") or d.get("codeFixAvailable") or d.get("fixable")):
            return d
    return items[0] if items and isinstance(items[0], dict) else None
