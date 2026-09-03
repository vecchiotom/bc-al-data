"""Deterministic corpus selection + record extraction over a cloned AL repo.

Selection is a pure function of the file path (sha1 bucketing) — no ranking,
no model, reproducible across machines.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from .alparse import objects, ALObject, Member

_ANALYZER_PREFIXES = ("AA", "AC", "AW", "DC", "FC", "LC", "PC", "TA", "UI")


def _split_hits(diags: list, start_row: int, end_row: int) -> tuple[list, list]:
    """Partition (code, severity, line) diagnostics whose 1-based line falls inside
    the member's 0-based [start_row, end_row] into (error_hits, analyzer_hits)."""
    errs: list = []
    analyzer: list = []
    for code, sev, line in diags:
        if start_row <= line - 1 <= end_row:
            entry = [code, sev, line]
            (analyzer if code[:2] in _ANALYZER_PREFIXES else errs).append(entry)
    return errs, analyzer


def select_files(root: Path, keep_one_in: int = 1, subdir: str = "src") -> list[Path]:
    base = root / subdir
    files = sorted(p for p in base.rglob("*.al") if p.is_file())
    if keep_one_in <= 1:
        return files
    picked = []
    for p in files:
        h = int.from_bytes(hashlib.sha1(str(p.relative_to(root)).encode()).digest()[:4], "big")
        if h % keep_one_in == 0:
            picked.append(p)
    return picked


@dataclass
class MemberRecord:
    repo: str
    path: str
    object_kind: str
    object_id: int | None
    object_name: str
    is_test: bool
    member_kind: str
    member_name: str
    is_local: bool
    signature: str
    doc_comment: str
    has_body: bool
    body: str
    body_loc: int
    member_text: str
    object_head: str          # object decl line + properties + var section (context, no member bodies)
    sibling_signatures: list[str]
    error_hits: list[list] = field(default_factory=list)      # [[code, severity, line], ...] AL#### diagnostics inside this member
    analyzer_hits: list[list] = field(default_factory=list)   # [[code, severity, line], ...] AA/AC/AW/DC/FC/LC/PC/TA/UI hits inside this member


def _object_head(obj: ALObject, src: bytes) -> str:
    # first line + properties block, up to the first member
    first_member = min((m.start_byte for m in obj.members), default=obj.end_byte)
    return src[obj.start_byte:first_member].decode("utf8", "replace").rstrip() + "\n"


def records_for_file(path: Path, repo: str, repo_root: Path,
                     diagnostics_by_path: dict[str, list] | None = None):
    """Yield member-record dicts for `path`.

    `diagnostics_by_path` maps an absolute resolved `.al` path to a list of
    `(code, severity, line)` triples (line 1-based); each triple is attributed to
    the member whose row span contains it and lands in `error_hits` (AL####) or
    `analyzer_hits` (analyzer rule ids)."""
    yield from (_r for _r in _records(path, repo, repo_root, diagnostics_by_path or {}))


def _records(path: Path, repo: str, repo_root: Path, diagnostics_by_path: dict[str, list]):
    src = path.read_bytes()
    file_diags = (diagnostics_by_path.get(str(path.resolve()))
                  or diagnostics_by_path.get(str(path)) or [])
    for obj in objects(src):
        head = _object_head(obj, src)
        sigs = [m.signature for m in obj.members]
        for m in obj.members:
            body = ""
            if m.body_start_byte is not None:
                body = src[m.body_start_byte:m.body_end_byte].decode("utf8", "replace")
            e_hits, a_hits = _split_hits(file_diags, m.start_row, m.end_row)
            yield asdict(MemberRecord(
                repo=repo, path=str(path.relative_to(repo_root)),
                object_kind=obj.kind, object_id=obj.obj_id, object_name=obj.name,
                is_test=obj.is_test, member_kind=m.kind, member_name=m.name,
                is_local=m.is_local, signature=m.signature, doc_comment=m.doc_comment,
                has_body=m.body_start_byte is not None, body=body,
                body_loc=body.count("\n") + 1 if body else 0,
                member_text=m.text, object_head=head, sibling_signatures=sigs,
                error_hits=e_hits, analyzer_hits=a_hits,
            ))


def build(root: Path, repo: str, keep_one_in: int, out: Path) -> dict:
    files = select_files(root, keep_one_in)
    n_obj = n_mem = 0
    with out.open("w") as fh:
        for f in files:
            try:
                for rec in records_for_file(f, repo, root):
                    fh.write(json.dumps(asdict(rec)) + "\n")
                    n_mem += 1
            except Exception as e:  # noqa: BLE001 - smoke: record and continue
                fh.write(json.dumps({"_parse_error": str(e), "path": str(f)}) + "\n")
    return {"files": len(files), "members": n_mem}
