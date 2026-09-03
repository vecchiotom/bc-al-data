"""G4 — doc-QA from the devitpro markdown.

Pure-Python tests over synthetic markdown: the section and prose filters keep
teaching content and drop link lists and navigational headings.
"""
from __future__ import annotations

from bcaldata import generators as G

_GOOD = """---
title: "AL error handling"
---

# AL error handling

## Using TryFunction methods

A try method catches an error so that execution can continue. The method returns
`false` when it traps an error, and `true` otherwise. Use it to model failure
without a full rollback.

```al
if not TryParse(Input) then
    Message('could not parse');
```

## See also

[Get Started with AL](devenv-get-started.md)
[Developing Extensions](devenv-dev-overview.md)
"""

_METHOD_PAGE = """---
title: "Record.SetRange(Any, Any, Any) Method"
---

# Record.SetRange(Any, Any, Any) Method
> **Version**: _Available or changed with runtime version 1.0._

Sets a simple filter on a field, selecting a single value or a range of values.
The filter replaces any existing filter on that field for the current record.

## Syntax
```AL
Record.SetRange(Field: Any [, FromValue: Any] [, ToValue: Any])
```

## Related information
[Record Data Type](record-data-type.md)
"""


def _run(name: str, text: str) -> list[dict]:
    return list(G.g4_docqa(f"dev-itpro/developer/{name}", text))


def test_keeps_only_the_teaching_section() -> None:
    out = _run("devenv-al-error-handling.md", _GOOD)
    assert len(out) == 1
    rec = out[0]
    assert rec["meta"]["heading"] == "Using TryFunction methods"
    assert rec["meta"]["doc_section"] == "developer"
    assert rec["messages"][0]["content"] == "In Business Central AL, explain Using TryFunction methods."
    assert "try method catches an error" in rec["messages"][1]["content"]


def test_drops_link_list_and_generic_headings() -> None:
    text = """# Page

## Related information

[a](a.md)
[b](b.md)
[c](c.md)

## Overview

[one](one.md)
[two](two.md)
"""
    assert _run("devenv-x.md", text) == []


def test_method_page_gets_a_reference_question() -> None:
    out = _run("methods-auto/record/record-setrange-any-any-any-method.md", _METHOD_PAGE)
    assert len(out) == 1
    q = out[0]["messages"][0]["content"]
    assert q == "How do I use the `Record.SetRange` method in Business Central AL? What does it do?"
    assert "SetRange(Field: Any" in out[0]["messages"][1]["content"]
    assert "Version" not in out[0]["messages"][1]["content"]


def test_non_developer_trees_are_skipped() -> None:
    assert list(G.g4_docqa("dev-itpro/administration/telemetry-x.md", _GOOD)) == []
    assert list(G.g4_docqa("dev-itpro/upgrade/upgrade-x.md", _GOOD)) == []
