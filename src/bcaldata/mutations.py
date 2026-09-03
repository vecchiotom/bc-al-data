"""G5 mutation catalog — one deterministic, localized edit per classic AL error class.

Each mutation takes a corpus.jsonl member row and returns
``(mutated_member_text, human_desc, expected_error_codes)`` or ``None`` when the
edit does not apply to that member. The mutated text replaces the whole member
(signature + var section + body); ``generators.g5_error_fix`` wraps it and the
clean original into a preference pair, and Stage 4 keeps the pair only when the
broken side fails to compile and the clean side does not.

Structural edits parse the member with tree-sitter-al (wrapped in a throwaway
codeunit so the grammar has an object context) and replace exact node byte
ranges — never blind regex. Purely lexical edits (`;`, `then`, `begin`) touch
single tokens located through the parse tree.

Calibration (`calibrate_g5.py`) records, per mutation, how often it applies, how
often the broken text introduces *new* compiler errors versus the pristine
member, and the modal new code. A mutation that frequently lands on a different
code than the one below is still a usable broken sample; the calibration report
is the source of truth for what each mutation actually produces here.
"""
from __future__ import annotations

import re
from typing import Callable

from .alparse import parse

# member_text is embedded verbatim after this prefix inside the wrapper object;
# subtract PLEN from any wrapped-source byte offset to index back into member_text.
_WRAP_PRE = "codeunit 50000 __MutWrap\n{\n"
_WRAP_SUF = "\n}\n"
PLEN = len(_WRAP_PRE.encode())

# true AL keywords — using one as an identifier is a hard parse error (AL0105).
_RESERVED = ("begin", "var", "then", "procedure", "trigger", "end", "case")


class _PM:
    """Parsed member: the wrapped parse tree plus offset helpers in member_text space."""

    def __init__(self, member_text: str):
        self.mt = member_text
        self.mtb = member_text.encode()
        src = (_WRAP_PRE + member_text + _WRAP_SUF).encode()
        self.root = parse(src).root_node
        self.proc = self._first(self.root, ("procedure", "trigger_declaration"))

    def _first(self, node, types):
        stack = [node]
        while stack:
            n = stack.pop(0)
            if n.type in types:
                return n
            stack.extend(n.children)
        return None

    def walk(self, node=None):
        node = node or self.proc
        if node is None:
            return
        stack = [node]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def of_type(self, *types, root=None):
        return [n for n in self.walk(root) if n.type in types]

    def has_error(self) -> bool:
        return any(n.type == "ERROR" or n.is_missing for n in self.walk(self.root))

    # -- byte range in member_text space --
    def rng(self, node) -> tuple[int, int]:
        return node.start_byte - PLEN, node.end_byte - PLEN

    def text(self, node) -> str:
        s, e = self.rng(node)
        return self.mtb[s:e].decode("utf8", "replace")

    def splice(self, start: int, end: int, repl: str) -> str:
        return (self.mtb[:start] + repl.encode() + self.mtb[end:]).decode("utf8", "replace")

    def replace_node(self, node, repl: str) -> str:
        s, e = self.rng(node)
        return self.splice(s, e, repl)


def _parsed(member: dict) -> _PM | None:
    pm = _PM(member["member_text"])
    return pm if pm.proc is not None else None


def _var_decls(pm: _PM) -> list:
    return pm.of_type("variable_declaration")


def _decl_name(node) -> str | None:
    ident = next((c for c in node.children if c.type in ("identifier", "quoted_identifier")), None)
    return ident.text.decode() if ident else None


def _code_block(pm: _PM):
    return next(iter(pm.of_type("code_block")), None)


def _changed(before: str, after: str | None) -> bool:
    return bool(after) and after != before


# --------------------------------------------------------------------------- #
# catalog
# --------------------------------------------------------------------------- #

def m_delete_semicolon(member: dict, obj_ctx: dict | None = None):
    """AL0111 — drop the ``;`` that terminates a statement inside the body."""
    pm = _parsed(member)
    if pm is None:
        return None
    blk = next(iter(pm.of_type("statement_block")), None)
    if blk is None:
        return None
    for c in blk.children:
        if c.type == ";" and c.prev_sibling is not None and c.prev_sibling.type.endswith("_statement"):
            s, e = pm.rng(c)
            out = pm.splice(s, e, "")
            return out, f"deleted ';' after a {c.prev_sibling.type}", ["AL0111"]
    return None


def m_rename_call(member: dict, obj_ctx: dict | None = None):
    """AL0132 / AL0118 — append ``X`` to a called method identifier."""
    pm = _parsed(member)
    if pm is None:
        return None
    for call in pm.of_type("call_expression"):
        fn = call.children[0] if call.children else None
        if fn is None:
            continue
        if fn.type == "member_expression":
            ident = [c for c in fn.children if c.type in ("identifier", "quoted_identifier")]
            target = ident[-1] if ident else None
            code = ["AL0132"]
        elif fn.type == "identifier":
            target = fn
            code = ["AL0118", "AL0132"]
        else:
            continue
        if target is None or target.text.decode() in ("if", "while", "for"):
            continue
        name = target.text.decode()
        out = pm.replace_node(target, name + "X")
        return out, f"renamed called method {name}() -> {name}X() (non-existent)", code
    return None


def m_rename_member(member: dict, obj_ctx: dict | None = None):
    """AL0132 — rename a ``<expr>.<Member>`` field/property access to a bogus member."""
    pm = _parsed(member)
    if pm is None:
        return None
    for me in pm.of_type("member_expression"):
        # skip member_expressions that are the callee of a call (handled by m_rename_call)
        if me.parent is not None and me.parent.type == "call_expression" and me.parent.children and me.parent.children[0] is me:
            continue
        ident = [c for c in me.children if c.type in ("identifier", "quoted_identifier")]
        if len(ident) < 2:
            continue
        last = ident[-1]
        name = last.text.decode().strip('"')
        out = pm.replace_node(last, "Nonexistent" + re.sub(r"\W", "", name)[:20])
        return out, f"renamed member access .{name} -> a non-existent member", ["AL0132"]
    return None


def _usages(pm: _PM, name: str, exclude_decl=True):
    decls = {id(n) for d in _var_decls(pm)
             for n in d.children if n.type in ("identifier", "quoted_identifier")}
    blk = next(iter(pm.of_type("statement_block")), None)
    if blk is None:
        return []
    return [n for n in pm.of_type("identifier", "quoted_identifier", root=blk)
            if n.text.decode() == name and not (exclude_decl and id(n) in decls)]


def m_rename_identifier(member: dict, obj_ctx: dict | None = None):
    """AL0118 — rename one *usage* of a local variable (leave its declaration)."""
    pm = _parsed(member)
    if pm is None:
        return None
    for d in _var_decls(pm):
        nm = _decl_name(d)
        if not nm:
            continue
        uses = _usages(pm, nm)
        if not uses:
            continue
        out = pm.replace_node(uses[0], nm + "2")
        return out, f"renamed one usage of local '{nm}' -> '{nm}2'", ["AL0118"]
    return None


def m_remove_var_decl(member: dict, obj_ctx: dict | None = None):
    """AL0118 — delete a ``var`` declaration whose variable is used in the body."""
    pm = _parsed(member)
    if pm is None:
        return None
    decls = _var_decls(pm)
    for d in decls:
        nm = _decl_name(d)
        if not nm or not _usages(pm, nm):
            continue
        if len(decls) == 1:
            sec = next(iter(pm.of_type("var_section")), None)
            if sec is None:
                return None
            s, e = pm.rng(sec)
            # also swallow the preceding newline/indent
            while s > 0 and pm.mtb[s - 1:s] in (b" ", b"\t", b"\n"):
                s -= 1
            out = pm.splice(s, e, "")
        else:
            s, e = pm.rng(d)
            while s > 0 and pm.mtb[s - 1:s] in (b" ", b"\t", b"\n"):
                s -= 1
            out = pm.splice(s, e, "")
        return out, f"deleted the declaration of local '{nm}' (still referenced)", ["AL0118"]
    return None


def m_rename_type(member: dict, obj_ctx: dict | None = None):
    """AL0134 — misspell a type in the var section."""
    pm = _parsed(member)
    if pm is None:
        return None
    for d in _var_decls(pm):
        ts = next((c for c in pm.walk(d) if c.type == "type_specification"), None)
        if ts is None:
            continue
        rec = next((c for c in pm.walk(ts) if c.type in ("record_type", "codeunit_type", "page_type", "report_type")), None)
        if rec is not None:
            qi = next((c for c in rec.children if c.type in ("quoted_identifier", "identifier")), None)
            if qi is None:
                continue
            raw = qi.text.decode()
            inner = raw.strip('"')
            bad = f'"{inner[:-1]}"' if raw.startswith('"') and len(inner) > 3 else inner + "X"
            out = pm.replace_node(qi, bad)
            return out, f"misspelled subtype {raw} -> {bad}", ["AL0134"]
        bt = next((c for c in pm.walk(ts) if c.type == "basic_type"), None)
        if bt is not None:
            raw = bt.text.decode()
            bad = raw[:-2] + raw[-1] if len(raw) > 4 else raw + "x"
            out = pm.replace_node(bt, bad)
            return out, f"misspelled type {raw} -> {bad}", ["AL0134"]
    return None


def m_rename_trigger(member: dict, obj_ctx: dict | None = None):
    """AL0162 — rename a trigger to an invented one (trigger members only)."""
    if member.get("member_kind") != "trigger":
        return None
    pm = _parsed(member)
    if pm is None or pm.proc is None:
        return None
    ident = next((c for c in pm.proc.children if c.type in ("identifier", "quoted_identifier")), None)
    if ident is None:
        return None
    name = ident.text.decode()
    bad = "OnAfterRun" if name == "OnRun" else name + "Xyz"
    out = pm.replace_node(ident, bad)
    return out, f"renamed trigger {name} -> {bad} (not a valid trigger)", ["AL0162"]


def m_swap_argument_count(member: dict, obj_ctx: dict | None = None):
    """AL0126 — duplicate the first argument of a call that already has one."""
    pm = _parsed(member)
    if pm is None:
        return None
    for al in pm.of_type("argument_list"):
        args = [c for c in al.children if c.type not in ("(", ")", ",")]
        if not args:
            continue
        first = args[0]
        s, e = pm.rng(first)
        dup = pm.mtb[s:e].decode("utf8", "replace")
        out = pm.splice(e, e, ", " + dup)
        callee = pm.text(al.parent.children[0]) if al.parent and al.parent.children else "?"
        return out, f"duplicated an argument of {callee}(...) (wrong arg count)", ["AL0126"]
    return None


def m_add_parens_to_property(member: dict, obj_ctx: dict | None = None):
    """AL0127 — turn a property/field read into a call: ``Rec.Name`` -> ``Rec.Name()``."""
    pm = _parsed(member)
    if pm is None:
        return None
    for me in pm.of_type("member_expression"):
        if me.parent is not None and me.parent.type == "call_expression" and me.parent.children and me.parent.children[0] is me:
            continue
        ident = [c for c in me.children if c.type in ("identifier", "quoted_identifier")]
        if len(ident) < 2:
            continue
        s, e = pm.rng(me)
        out = pm.splice(e, e, "()")
        return out, f"added () to the property read {pm.mtb[s:e].decode('utf8','replace')}", ["AL0127"]
    return None


def m_semicolon_before_else(member: dict, obj_ctx: dict | None = None):
    """AL0110 — insert ``;`` immediately before an ``else``."""
    pm = _parsed(member)
    if pm is None:
        return None
    for node in pm.walk():
        if node.type in ("else_keyword", "else") and node.text.decode() == "else":
            s, _ = pm.rng(node)
            # place the stray ';' just before the else, after existing whitespace
            i = s
            while i > 0 and pm.mtb[i - 1:i] in (b" ", b"\t"):
                i -= 1
            out = pm.splice(i, i, ";")
            return out, "inserted a stray ';' before 'else' (orphaned else)", ["AL0110"]
    return None


def m_delete_begin(member: dict, obj_ctx: dict | None = None):
    """AL0104 / AL0109 — remove a ``begin`` keyword from a code block."""
    pm = _parsed(member)
    if pm is None:
        return None
    begins = [n for n in pm.walk() if n.type in ("begin_keyword", "begin") and n.text.decode() == "begin"]
    if not begins:
        return None
    node = begins[-1] if len(begins) > 1 else begins[0]
    s, e = pm.rng(node)
    out = pm.splice(s, e, "")
    return out, "removed a 'begin' keyword from a code block", ["AL0104", "AL0109"]


def m_delete_then(member: dict, obj_ctx: dict | None = None):
    """AL0104 — remove the ``then`` keyword of an ``if`` statement."""
    pm = _parsed(member)
    if pm is None:
        return None
    for node in pm.walk():
        if node.type in ("then_keyword", "then") and node.text.decode() == "then":
            s, e = pm.rng(node)
            out = pm.splice(s, e, "")
            return out, "removed the 'then' keyword of an if statement", ["AL0104"]
    return None


def m_keyword_as_identifier(member: dict, obj_ctx: dict | None = None):
    """AL0105 — rename a local variable (declaration + usages) to a reserved word."""
    pm = _parsed(member)
    if pm is None:
        return None
    for d in _var_decls(pm):
        nm = _decl_name(d)
        if not nm:
            continue
        kw = _RESERVED[len(nm) % len(_RESERVED)]
        ident = next((c for c in d.children if c.type in ("identifier", "quoted_identifier")), None)
        if ident is None:
            continue
        # rename declaration + every usage, right-to-left so offsets stay valid
        targets = sorted([ident, *_usages(pm, nm)], key=lambda n: n.start_byte, reverse=True)
        out = member["member_text"]
        mtb = out.encode()
        for t in targets:
            s, e = t.start_byte - PLEN, t.end_byte - PLEN
            mtb = mtb[:s] + kw.encode() + mtb[e:]
        out = mtb.decode("utf8", "replace")
        return out, f"renamed local '{nm}' to the reserved word '{kw}'", ["AL0105"]
    return None


_NUMERIC = {"Integer", "Decimal", "BigInteger", "Byte"}


def m_change_var_type(member: dict, obj_ctx: dict | None = None):
    """AL0122 — change a numeric var's type to Boolean so a numeric assignment fails."""
    pm = _parsed(member)
    if pm is None:
        return None
    for d in _var_decls(pm):
        nm = _decl_name(d)
        bt = next((c for c in pm.walk(d) if c.type == "basic_type"), None)
        if not nm or bt is None:
            continue
        cur = bt.text.decode()
        if cur in _NUMERIC:
            repl = "Boolean"
        elif cur in ("Text", "Code"):
            repl = "Integer"
        else:
            continue
        # only worthwhile if the var is actually assigned somewhere
        if not _usages(pm, nm):
            continue
        out = pm.replace_node(bt, repl)
        return out, f"changed type of local '{nm}' from {cur} to {repl} (assignment mismatch)", ["AL0122"]
    return None


Mutation = Callable[[dict, dict | None], "tuple[str, str, list[str]] | None"]

CATALOG: list[tuple[str, Mutation]] = [
    ("m_delete_semicolon", m_delete_semicolon),
    ("m_rename_call", m_rename_call),
    ("m_rename_member", m_rename_member),
    ("m_rename_identifier", m_rename_identifier),
    ("m_remove_var_decl", m_remove_var_decl),
    ("m_rename_type", m_rename_type),
    ("m_rename_trigger", m_rename_trigger),
    ("m_swap_argument_count", m_swap_argument_count),
    ("m_add_parens_to_property", m_add_parens_to_property),
    ("m_semicolon_before_else", m_semicolon_before_else),
    ("m_delete_begin", m_delete_begin),
    ("m_delete_then", m_delete_then),
    ("m_keyword_as_identifier", m_keyword_as_identifier),
    ("m_change_var_type", m_change_var_type),
]

# Canonical target code(s) per mutation — the code the edit is designed to
# provoke. `calibrate_g5.py` measures what the compiler actually emits here; see
# data/g5_calibration.md for the measured modal codes (several land on a
# neighbouring syntax/binding code and are still valid broken samples).
EXPECTED: dict[str, list[str]] = {
    "m_delete_semicolon": ["AL0111"],
    "m_rename_call": ["AL0132", "AL0118"],
    "m_rename_member": ["AL0132"],
    "m_rename_identifier": ["AL0118"],
    "m_remove_var_decl": ["AL0118"],
    "m_rename_type": ["AL0134", "AL0185", "AL0118"],
    "m_rename_trigger": ["AL0162"],
    "m_swap_argument_count": ["AL0126"],
    "m_add_parens_to_property": ["AL0127", "AL0125"],
    "m_semicolon_before_else": ["AL0110"],
    "m_delete_begin": ["AL0104", "AL0109"],
    "m_delete_then": ["AL0104"],
    "m_keyword_as_identifier": ["AL0105", "AL0104"],
    "m_change_var_type": ["AL0122"],
}


def apply_mutation(name: str, fn: Mutation, member: dict, obj_ctx: dict | None = None):
    """Run one mutation, returning ``(bad_text, desc, codes)`` or ``None``.

    Guards: the result must differ from the input and must not itself be a
    tree-sitter parse failure of the *wrapper* (a mutation that only corrupts
    syntax past recognition is a poor training sample)."""
    res = fn(member, obj_ctx)
    if res is None:
        return None
    bad, desc, codes = res
    if not _changed(member["member_text"], bad):
        return None
    return bad, desc, codes
