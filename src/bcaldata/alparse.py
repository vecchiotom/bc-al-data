"""Deterministic AL structure extraction via tree-sitter-al.

One object per `*_declaration` node under `source_file`; members are `procedure`
and `trigger_declaration` nodes under the object's `declaration_body`.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from functools import cache
import tree_sitter_al as tsal
import tree_sitter as ts

OBJECT_DECL = {
    "codeunit_declaration", "table_declaration", "tableextension_declaration",
    "page_declaration", "pageextension_declaration", "report_declaration",
    "reportextension_declaration", "xmlport_declaration", "query_declaration",
    "enum_declaration", "enumextension_declaration", "interface_declaration",
    "permissionset_declaration", "permissionsetextension_declaration",
    "controladdin_declaration", "entitlement_declaration", "profile_declaration",
    "pagecustomization_declaration",
}
MEMBER = {"procedure", "trigger_declaration"}


@cache
def _parser() -> ts.Parser:
    return ts.Parser(ts.Language(tsal.language()))


def parse(src: bytes) -> ts.Tree:
    return _parser().parse(src)


def _txt(n: ts.Node) -> str:
    return n.text.decode("utf8", "replace")


@dataclass
class Member:
    kind: str                # "procedure" | "trigger"
    name: str
    is_local: bool
    signature: str           # first line up to the return type / paren close
    header_end_byte: int     # byte offset where the body block starts (after 'begin' region)
    start_byte: int
    end_byte: int
    start_row: int
    end_row: int
    body_start_byte: int | None
    body_end_byte: int | None
    attributes: list[str] = field(default_factory=list)
    doc_comment: str = ""
    text: str = ""


@dataclass
class ALObject:
    kind: str                # "codeunit", "table", ...
    obj_id: int | None
    name: str
    start_byte: int
    end_byte: int
    text: str
    members: list[Member] = field(default_factory=list)
    is_test: bool = False
    properties: dict[str, str] = field(default_factory=dict)


_NAME_RE = re.compile(r'^\s*(?P<local>local\s+|internal\s+|protected\s+)*'
                      r'(?:procedure|trigger)\s+(?P<name>"[^"]+"|\w+)', re.I)


def _leading_doc_comment(node: ts.Node, src: bytes) -> str:
    """Comment lines directly above `node`, walking up while each pair is adjacent
    (no blank line between). Attribute items in between are skipped."""
    lines: list[str] = []
    anchor = node
    prev = node.prev_sibling
    while prev is not None and prev.type in ("comment", "attribute_item"):
        if prev.type == "comment":
            gap = src[prev.end_byte:anchor.start_byte].count(b"\n")
            if gap > 1:
                break
            lines.insert(0, _txt(prev))
        anchor = prev
        prev = prev.prev_sibling
    return "\n".join(lines).strip()


def _collect_attrs(node: ts.Node) -> list[str]:
    attrs, prev = [], node.prev_sibling
    while prev is not None and prev.type in ("attribute_item", "comment"):
        if prev.type == "attribute_item":
            attrs.insert(0, _txt(prev))
        prev = prev.prev_sibling
    return attrs


def _member(node: ts.Node, src: bytes) -> Member | None:
    raw = _txt(node)
    ident = next((c for c in node.children if c.type in ("identifier", "quoted_identifier")), None)
    if ident is None:
        return None
    name = _txt(ident).strip('"')
    is_local = any(c.type == "procedure_modifier" and _txt(c).lower() in ("local", "internal", "protected")
                   for c in node.children)
    body = next((c for c in node.children if c.type == "code_block"), None)
    var_sec = next((c for c in node.children if c.type == "var_section"), None)
    body_end = None
    if body is not None:
        # include the ';' that terminates the procedure, if present
        nxt = body.next_sibling
        body_end = nxt.end_byte if (nxt is not None and _txt(nxt) == ";") else body.end_byte
    # signature = from node start to the start of var_section / code_block
    sig_end = min([c.start_byte for c in (var_sec, body) if c is not None] or [node.end_byte])
    signature = src[node.start_byte:sig_end].decode("utf8", "replace").strip().rstrip("{").strip()
    return Member(
        kind="trigger" if node.type == "trigger_declaration" else "procedure",
        name=name, is_local=is_local, signature=signature,
        header_end_byte=sig_end,
        start_byte=node.start_byte, end_byte=node.end_byte,
        start_row=node.start_point[0], end_row=node.end_point[0],
        body_start_byte=body.start_byte if body else None,
        body_end_byte=body_end,
        attributes=_collect_attrs(node), doc_comment=_leading_doc_comment(node, src), text=raw,
    )


def objects(src: bytes) -> list[ALObject]:
    tree = parse(src)
    out: list[ALObject] = []
    for node in tree.root_node.children:
        if node.type not in OBJECT_DECL:
            continue
        kind = node.type.removesuffix("_declaration")
        obj_id = None
        name = "?"
        for c in node.children:
            if c.type == "integer" and obj_id is None:
                obj_id = int(_txt(c))
            elif c.type in ("quoted_identifier", "identifier") and name == "?":
                name = _txt(c).strip('"')
        body = next((c for c in node.children if c.type == "declaration_body"), None)
        props: dict[str, str] = {}
        members: list[Member] = []
        if body:
            for c in body.children:
                if c.type == "property":
                    pm = re.match(r'\s*(\w+)\s*=\s*(.+?);', _txt(c))
                    if pm:
                        props[pm.group(1)] = pm.group(2).strip()
                elif c.type in MEMBER:
                    mem = _member(c, src)
                    if mem:
                        members.append(mem)
        out.append(ALObject(
            kind=kind, obj_id=obj_id, name=name,
            start_byte=node.start_byte, end_byte=node.end_byte, text=_txt(node),
            members=members,
            is_test=props.get("Subtype", "").lower() == "test",
            properties=props,
        ))
    return out
