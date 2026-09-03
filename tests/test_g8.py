"""G8 — analyzer warning -> clean AL.

Pure-Python tests cover the candidate shape. The `slow` tests drive the ALCops
MCP server (built at `bin/alcops-mcp` / `vendor/mcp-server`); they skip when it
is unavailable or the AL toolchain is missing.
"""
from __future__ import annotations

import json
import shutil

import pytest

from bcaldata import generators as G
from bcaldata.generate_g8 import CORPUS, _member_text, run_g8
from bcaldata.mcp_client import ALCopsMcp, alcops_mcp_command
from conftest import SMOKE_APP, _needs_toolchain

pytestmark = pytest.mark.timeout(1200)

_HAS_ALCOPS = alcops_mcp_command() is not None


def _rec(**over) -> dict:
    base = dict(
        repo="x/y", path="src/Foo.Codeunit.al", object_kind="codeunit", object_id=50000,
        object_name="Foo", is_test=False, member_kind="procedure", member_name="Bar",
        is_local=False, signature="procedure Bar()", doc_comment="", has_body=True,
        body="begin\n    Rec.Init();\nend;", body_loc=3,
        member_text="procedure Bar()\n    begin\n        Rec.Init();\n    end;",
        object_head="codeunit 50000 Foo\n{", sibling_signatures=["procedure Bar()"],
        error_hits=[], analyzer_hits=[["PC0037", "warning", 3]],
    )
    base.update(over)
    return base


# ---- candidate shape (no toolchain) ---------------------------------------

def test_g8_review_lists_findings_with_templates():
    cands = list(G.g8_review(_rec(), message_templates={"PC0037": "Use Validate() instead."}))
    assert len(cands) == 1
    c = cands[0]
    assert c["gen"] == "g8_review" and c["rules"] == ["PC0037"]
    assert "PC0037" in c["messages"][1]["content"]
    assert "Use Validate() instead." in c["messages"][1]["content"]
    assert c["target_al"] is None


def test_g8_warning_clean_needs_a_real_change():
    rec = _rec()
    good = f"{rec['signature']}\n{rec['body']}"
    assert list(G.g8_warning_clean(rec, fixed_text=None)) == []
    assert list(G.g8_warning_clean(rec, fixed_text=good)) == []  # unchanged -> no row
    fixed = good.replace("Rec.Init()", "Rec.Validate(Name)")
    cands = list(G.g8_warning_clean(rec, fixed_text=fixed, applied_rules=["PC0037"]))
    assert len(cands) == 1
    c = cands[0]
    assert c["gen"] == "g8_warning_clean"
    assert c["rejected_al"] == good and c["target_al"] == fixed.strip()
    assert c["rules"] == ["PC0037"]


def test_g8_review_skips_member_without_hits():
    assert list(G.g8_review(_rec(analyzer_hits=[]))) == []


# ---- ALCops MCP roundtrip -----------------------------------------------

@pytest.mark.slow
@pytest.mark.skipif(not _HAS_ALCOPS, reason="alcops-mcp not built")
def test_alcops_analyze_and_apply_fix_change_a_file(tmp_path):
    reason = _needs_toolchain()
    if reason:
        pytest.skip(reason)
    dst = tmp_path / "app"
    shutil.copytree(SMOKE_APP, dst, ignore=shutil.ignore_patterns(".alpackages", "*.app"))
    from bcaldata.verify import _shared_alpackages

    (dst / ".alpackages").symlink_to(_shared_alpackages())
    # FC0002: `record` must be cased `Record` — a rule with a working code fix.
    f = dst / "src" / "Casing.Codeunit.al"
    f.write_text('codeunit 50010 "Casing Probe"\n{\n    trigger OnRun()\n    var\n'
                 '        Cust: record Customer;\n    begin\n        Cust.Init();\n    end;\n}\n')
    before = f.read_text()

    with ALCopsMcp(timeout=600) as ac:
        mcp = ac.mcp
        an = mcp.call_tool_json("analyze", {"projectPath": str(dst), "filePath": str(f)})
        fc = [d for d in an.get("diagnostics", [])
              if d["id"] == "FC0002" and d.get("hasCodeFix")]
        assert fc, an
        d = fc[0]
        fixes = mcp.call_tool_json(
            "get_fixes", {"projectPath": str(dst), "filePath": str(f),
                          "diagnosticId": "FC0002", "line": d["startLine"], "column": d["startColumn"]})
        keys = [x["equivalenceKey"] for x in fixes if x.get("equivalenceKey")]
        assert keys, fixes
        res = mcp.call_tool_json(
            "apply_fix", {"projectPath": str(dst), "filePath": str(f), "diagnosticId": "FC0002",
                          "line": d["startLine"], "column": d["startColumn"], "equivalenceKey": keys[0]})
        assert res.get("applied") is True, res

    after = f.read_text()
    assert after != before
    assert "Record Customer" in after


def test_member_text_roundtrips_a_procedure():
    src = ('codeunit 50000 "X"\n{\n    procedure Bar(): Integer\n    begin\n'
           '        exit(1);\n    end;\n}\n').encode()
    mt = _member_text(src, "Bar")
    assert mt is not None and mt.startswith("procedure Bar(): Integer")
    assert "exit(1);" in mt


# ---- end-to-end ---------------------------------------------------------

@pytest.mark.slow
@pytest.mark.skipif(not _HAS_ALCOPS, reason="alcops-mcp not built")
def test_run_g8_produces_candidates(tmp_path):
    if not CORPUS.exists():
        pytest.skip("data/corpus.jsonl not built")
    rows = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()]
    attributed = [r for r in rows if r.get("analyzer_hits") and r.get("app_dir")]
    if not attributed:
        pytest.skip("no attributed corpus rows with app_dir (run build_baseline_and_corpus_mini)")
    stats = run_g8(limit=8, out_dir=tmp_path)  # tmp_path: never clobber data/candidates/
    assert stats["g8_review"] >= 1
    assert stats["members"] >= 1
