"""Auto-fixer unit tests.

Pure-Python strategy tests run always; end-to-end tests that shell out to the AL
compiler are marked `slow`.
"""
from __future__ import annotations

import pytest

from bcaldata.autofix import (
    _levenshtein, _nearest, _rename_word, _structural, _near_name, autofix,
)


def test_levenshtein():
    assert _levenshtein("Foo", "Foo") == 0
    assert _levenshtein("FooX", "Foo") == 1
    assert _levenshtein("Fooo", "Foo") == 1
    assert _levenshtein("abcdef", "xyz") == 3  # clamped, >2


def test_nearest_single_candidate():
    assert _nearest("InsertFileContentX", {"InsertFileContent", "GetFromLog"}) == "InsertFileContent"
    # two equally-near candidates -> ambiguous -> None
    assert _nearest("Test", {"Best", "Rest", "Nest"}) is None


def test_rename_word_is_whole_word():
    assert _rename_word("x := Foo() + FooBar();", "Foo", "Bar") == "x := Bar() + FooBar();"


def test_structural_missing_semicolon():
    err = {"code": "AL0111", "startLine": 3, "startColumn": 30, "message": "Semicolon expected."}
    text = "procedure P()\nbegin\n    exit(InsertFileContent())\nend;"
    out = _structural(text, err)
    assert out is not None and "InsertFileContent());" in out


def test_structural_semicolon_before_else_regex():
    err = {"code": "AL0110", "startLine": 1, "startColumn": 1, "message": "Orphaned ELSE"}
    text = "if X then\n    Y();\nelse\n    Z();"
    assert _structural(text, err) == "if X then\n    Y()\nelse\n    Z();"
    text2 = "if X then Y(); else Z();"
    assert _structural(text2, err) == "if X then Y() else Z();"
    assert _structural("x := 1;\ny := 2;", err) is None


def test_structural_bad_using():
    err = {"code": "AL0791", "startLine": 1, "startColumn": 1,
           "message": "The namespace 'Foo.Bar.Baz' is unknown."}
    text = "using Foo.Bar.Baz;\nusing System.Utilities;\ncodeunit 50000 X\n{\n}"
    out = _structural(text, err)
    assert out is not None and "Foo.Bar.Baz" not in out and "System.Utilities" in out


def test_structural_keyword_as_identifier():
    err = {"code": "AL0105", "startLine": 1, "startColumn": 10,
           "message": "Syntax error, identifier expected; 'exit' is a keyword"}
    text = "var\n    exit: Integer;\nbegin\n    exit := 1;\nend;"
    out = _structural(text, err)
    assert out is not None and "exitValue" in out


def test_near_name_undoes_suffix():
    err = {"code": "AL0118", "startLine": 1, "startColumn": 1,
           "message": "The name 'CustNo2' does not exist in the current context."}
    text = "var\n    CustNo: Code[20];\nbegin\n    Message(CustNo2);\nend;"
    out = _near_name(text, err, None)
    assert out is not None and "CustNo2" not in out and "Message(CustNo)" in out


def test_near_name_trigger():
    err = {"code": "AL0162", "startLine": 1, "startColumn": 1,
           "message": "'OnAfterGetRecrd' is not a valid trigger for this object type."}
    text = "trigger OnAfterGetRecrd()\nbegin\nend;"
    out = _near_name(text, err, None)
    assert out is not None and "OnAfterGetRecord" in out


@pytest.mark.slow
def test_autofix_missing_semicolon_end_to_end():
    broken = "procedure Demo()\nvar\n    I: Integer;\nbegin\n    I := 1 + 2\n    I := I + 1;\nend;"
    fixed, method = autofix(broken, [{"severity": "error", "code": "AL0111", "message": "Semicolon expected."}])
    assert fixed is not None and "structural" in method
    assert "1 + 2;" in fixed


@pytest.mark.slow
def test_autofix_orphaned_else_end_to_end():
    broken = "procedure Demo()\nvar\n    X: Boolean;\nbegin\n    if X then\n        X := false;\n    else\n        X := true;\nend;"
    fixed, method = autofix(broken, [{"severity": "error", "code": "AL0110", "message": "Orphaned ELSE"}])
    assert fixed is not None
