"""Unit coverage for the G5 mutation catalog.

Every mutation: a hand-written clean AL member, assert it applies and changes
the text. A representative subset also asserts the broken text fails to compile
(marked ``slow`` — cold ``al compile``).
"""
from __future__ import annotations

import pytest

from bcaldata import mutations as M

# --- fixture members -------------------------------------------------------- #

PROC_VARS = """procedure ComputeTotal(DocNo: Code[20]): Decimal
    var
        SalesLine: Record "Sales Line";
        Total: Decimal;
        Factor: Integer;
    begin
        Factor := 2;
        SalesLine.SetRange("Document No.", DocNo);
        if SalesLine.FindSet() then
            repeat
                Total := Total + SalesLine.Amount;
            until SalesLine.Next() = 0;
        Message(SalesLine.Description);
        exit(Total * Factor);
    end;"""

PROC_ELSE = """procedure PickLabel(Flag: Boolean): Text
    var
        Result: Text;
    begin
        if Flag then
            Result := 'yes'
        else
            Result := 'no';
        exit(Result);
    end;"""

TRIGGER = """trigger OnRun()
    var
        Setup: Record "Sales & Receivables Setup";
    begin
        Setup.Get();
        Setup.TestField("Stockout Warning");
    end;"""


def _member(text: str, kind: str = "procedure") -> dict:
    return {"member_text": text, "member_kind": kind, "object_kind": "codeunit",
            "object_name": "Test", "object_head": "codeunit 50000 Test", "body": text,
            "body_loc": text.count("\n") + 1, "is_test": False, "has_body": True}


CASES = {
    "m_delete_semicolon": PROC_VARS,
    "m_rename_call": PROC_VARS,
    "m_rename_member": PROC_VARS,
    "m_rename_identifier": PROC_VARS,
    "m_remove_var_decl": PROC_VARS,
    "m_rename_type": PROC_VARS,
    "m_rename_trigger": TRIGGER,
    "m_swap_argument_count": PROC_VARS,
    "m_add_parens_to_property": PROC_VARS,
    "m_semicolon_before_else": PROC_ELSE,
    "m_delete_begin": PROC_VARS,
    "m_delete_then": PROC_VARS,
    "m_keyword_as_identifier": PROC_VARS,
    "m_change_var_type": PROC_VARS,
}

_FNS = dict(M.CATALOG)


def test_catalog_has_at_least_ten_mutations():
    assert len(M.CATALOG) >= 10
    assert len({n for n, _ in M.CATALOG}) == len(M.CATALOG)


@pytest.mark.parametrize("name", list(CASES))
def test_mutation_applies_and_changes_text(name):
    text = CASES[name]
    kind = "trigger" if text.lstrip().startswith("trigger") else "procedure"
    member = _member(text, kind)
    res = M.apply_mutation(name, _FNS[name], member)
    assert res is not None, f"{name} did not apply to its fixture"
    bad, desc, codes = res
    assert bad != text
    assert isinstance(desc, str) and desc
    assert codes and all(c.startswith("AL") for c in codes)


def test_trigger_only_mutation_skips_procedures():
    assert M.apply_mutation("m_rename_trigger", M.m_rename_trigger, _member(PROC_VARS)) is None


def test_non_applicable_returns_none():
    tiny = _member("procedure Noop()\n    begin\n    end;")
    assert M.apply_mutation("m_remove_var_decl", M.m_remove_var_decl, tiny) is None
    assert M.apply_mutation("m_rename_identifier", M.m_rename_identifier, tiny) is None


# --- compile checks (slow) ------------------------------------------------- #

_COMPILE_SUBSET = [
    "m_delete_semicolon",
    "m_rename_call",
    "m_delete_then",
    "m_add_parens_to_property",
]


@pytest.mark.slow
@pytest.mark.parametrize("name", _COMPILE_SUBSET)
def test_mutation_breaks_compile(name):
    from bcaldata.verify import _compile_snippet

    text = CASES[name]
    member = _member(text)
    clean = _compile_snippet(text)
    if not clean.clean:
        pytest.skip(f"fixture for {name} is not clean out of context: {clean.errors[:2]}")
    bad, _desc, _codes = M.apply_mutation(name, _FNS[name], member)
    assert not _compile_snippet(bad).clean, f"{name} left the member compiling"
