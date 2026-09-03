"""G7 hard-negative wiring (no model, no toolchain): rollout -> pair -> autofix."""
from __future__ import annotations
import types

from bcaldata import generators as G
from bcaldata.generate import _apply_autofix, _extract_al


def _fake_compile(clean: bool, diags):
    return types.SimpleNamespace(clean=clean, diagnostics=diags,
                                 errors=[c for s, c, _ in diags if s == "error"])


def test_extract_al_prefers_al_fence():
    assert _extract_al("text\n```al\nprocedure X() begin end;\n```\n") == "procedure X() begin end;"
    assert _extract_al("```\nfoo\n```") == "foo"
    assert _extract_al("no fence") is None


def test_rollout_keeps_only_non_compiling_completion():
    probe = {"messages": [{"role": "user", "content": "Implement Foo"}],
             "gold": "procedure Foo() begin exit(1) end;", "probe_of": "g1_fim",
             "meta": {"repo": "microsoft/BCApps", "path": "src/App/A.al", "member": "Foo"}}
    assert G.g7_from_rollout(probe, "procedure Foo() begin exit(1) end;",
                             _fake_compile(True, [])) is None
    pair = G.g7_from_rollout(probe, "procedure Foo() begin exit(Bxr()) end;",
                             _fake_compile(False, [("error", "AL0132", "no method Bxr")]))
    assert pair["gen"] == "g7_hard_negative"
    assert pair["rejected_al"] == "procedure Foo() begin exit(Bxr()) end;"
    assert pair["target_al"] == probe["gold"]


def test_apply_autofix_swaps_chosen_to_the_repair_when_one_exists():
    pair = {"messages": [{"role": "user", "content": "Implement Foo"},
                         {"role": "assistant", "content": "```al\ngold\n```"}],
            "target_al": "gold", "rejected_al": "broken", "meta": {"member": "Foo"}}
    _apply_autofix(pair, "broken", _fake_compile(False, [("error", "AL0111", ";")]),
                   lambda al, d: ("broken;", "structural:AL0111"))
    assert pair["chosen"] == "broken;" and pair["rejected"] == "broken"
    assert pair["meta"]["autofixed"] is True

    pair2 = {"messages": [{"role": "user", "content": "x"},
                          {"role": "assistant", "content": "```al\ngold\n```"}],
             "target_al": "gold", "rejected_al": "broken", "meta": {"member": "Foo"}}
    _apply_autofix(pair2, "broken", _fake_compile(False, []), lambda al, d: (None, "unfixable"))
    assert pair2["chosen"] == "gold" and pair2["meta"]["autofixed"] is False
