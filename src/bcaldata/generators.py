"""Deterministic training-example generators over MemberRecord dicts.

Each generator yields candidate dicts:
  {"gen", "messages":[{role,content}...], "target_al", "meta":{...}}
No model calls. G3 uses a template (a real run would paraphrase with an LLM).
G5 returns preference pairs. Compile verification happens downstream.
"""
from __future__ import annotations
import re
from typing import Iterator

_CALL = re.compile(r'\b([A-Z][A-Za-z0-9_]*)\s*\(')
_RECORD = re.compile(r'\bRecord\s+("[^"]+"|\w+)')
_FENCE = "```al\n{}\n```"


def _ctx(rec: dict) -> str:
    sibs = "\n".join(f"    {s};" for s in rec["sibling_signatures"] if s != rec["signature"])
    return rec["object_head"].rstrip() + ("\n\n    // other members:\n" + sibs if sibs else "")


def _usable_body(rec: dict, lo=3, hi=45) -> bool:
    return (rec["has_body"] and not rec["is_test"]
            and lo <= rec["body_loc"] <= hi
            and rec["member_kind"] == "procedure"
            and "begin" in rec["body"])


# ---------------- G1: fill-in-the-middle procedure body ----------------
def g1_fim(rec: dict) -> Iterator[dict]:
    if not _usable_body(rec):
        return
    prompt = (
        f"Complete the body of `{rec['member_name']}` in this AL "
        f"{rec['object_kind']}. Return only the full procedure.\n\n"
        f"{_FENCE.format(_ctx(rec))}\n\n"
        f"Procedure to implement:\n{_FENCE.format(rec['signature'])}"
    )
    target = f"{rec['signature']}\n{rec['body']}"
    yield {"gen": "g1_fim",
           "messages": [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": _FENCE.format(target)}],
           "target_al": target,
           "meta": {"repo": rec["repo"], "path": rec["path"],
                    "object": f"{rec['object_kind']} {rec['object_name']}",
                    "member": rec["member_name"]}}


# ---------------- G2: intent (doc-comment) -> implementation ----------------
def g2_sig2body(rec: dict) -> Iterator[dict]:
    doc = rec["doc_comment"].strip()
    doc_clean = re.sub(r'^\s*//+\s?', '', doc, flags=re.M).strip()
    if not _usable_body(rec) or len(doc_clean) < 25 or doc_clean.lower().startswith(("todo", "wip")):
        return
    prompt = (
        f"Implement this AL procedure in {rec['object_kind']} "
        f"\"{rec['object_name']}\".\n\nIntent:\n{doc_clean}\n\n"
        f"Signature:\n{_FENCE.format(rec['signature'])}"
    )
    target = f"{rec['signature']}\n{rec['body']}"
    yield {"gen": "g2_sig2body",
           "messages": [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": _FENCE.format(target)}],
           "target_al": target,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"]}}


# ---------------- G3: explain / review (deterministic template) ----------------
def g3_explain(rec: dict) -> Iterator[dict]:
    if not rec["has_body"] or rec["body_loc"] < 4:
        return
    body = rec["body"]
    calls = sorted({m for m in _CALL.findall(body)} - {"if", "for", "while", "case", "then"})
    recs = sorted({m.strip('"') for m in _RECORD.findall(rec["member_text"])})
    ret = ""
    mret = re.search(r'\)\s*:\s*(.+)$', rec["signature"])
    if mret:
        ret = mret.group(1).strip()
    parts = [f"`{rec['member_name']}` is a{'n internal' if rec['is_local'] else ''} "
             f"{rec['member_kind']} on {rec['object_kind']} \"{rec['object_name']}\"."]
    if recs:
        parts.append(f"It works with the record type(s): {', '.join(recs)}.")
    if calls:
        parts.append(f"It calls: {', '.join(calls[:12])}.")
    if ret:
        parts.append(f"It returns `{ret}`.")
    answer = " ".join(parts)
    prompt = f"Explain what this AL procedure does.\n\n{_FENCE.format(rec['member_text'])}"
    yield {"gen": "g3_explain",
           "messages": [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": answer}],
           "target_al": None,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                    "template": True}}


# ---------------- G5: error -> fix (preference pairs, deterministic mutation) ----------------
def _mut_rename_call(body: str):
    for m in _CALL.finditer(body):
        name = m.group(1)
        if name in ("if", "for", "while", "case", "Message", "Error"):
            continue
        bad = name + "X"
        return body[:m.start(1)] + bad + body[m.end(1):], f"renamed call {name}() -> {bad}() (non-existent)"
    return None


def _mut_drop_semicolon(body: str):
    lines = body.split("\n")
    for i, ln in enumerate(lines):
        s = ln.rstrip()
        if s.endswith(";") and not s.strip().startswith("//") and len(s.strip()) > 6:
            lines[i] = s[:-1]
            return "\n".join(lines), f"dropped ';' at line {i+1} (structural)"
    return None


_MUTATIONS = [("m_rename_call", _mut_rename_call), ("m_drop_semicolon", _mut_drop_semicolon)]


def g5_error_fix(rec: dict) -> Iterator[dict]:
    if not _usable_body(rec) or rec["body_loc"] > 30:
        return
    good = f"{rec['signature']}\n{rec['body']}"
    for mid, fn in _MUTATIONS:
        res = fn(rec["body"])
        if res is None:
            continue
        bad_body, desc = res
        bad = f"{rec['signature']}\n{bad_body}"
        if bad == good:
            continue
        yield {"gen": "g5_error_fix", "mutation": mid,
               "messages": [{"role": "user",
                             "content": f"This AL does not compile. Fix it.\n\n{_FENCE.format(bad)}"},
                            {"role": "assistant", "content": _FENCE.format(good)}],
               "target_al": good, "rejected_al": bad,
               "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                        "mutation_desc": desc, "expected_diagnostic": "TBD-calibrate"}}


# ---------------- G6: spec -> object (small self-contained objects) ----------------
def g6_spec2object(rec: dict) -> Iterator[dict]:
    # runs once per object: only fire on the first member to dedupe
    if rec["object_kind"] not in ("enum", "table") or rec["member_name"] != (rec["sibling_signatures"][0:1] or [""])[0]:
        return
    # handled in object-level generator instead; keep empty here
    return


def object_level_g6(obj_text: str, kind: str, obj_id, name: str, repo: str, path: str) -> Iterator[dict]:
    if kind not in ("enum", "table"):
        return
    if obj_text.count("\n") > 60:
        return
    head = obj_text.split("{", 1)[0].strip()
    fields = re.findall(r'\bfield\(\s*\d+\s*;\s*("[^"]+"|\w+)\s*;\s*([^)]+)\)', obj_text)
    values = re.findall(r'\bvalue\(\s*\d+\s*;\s*("[^"]+"|\w+)\s*\)', obj_text)
    if kind == "table" and fields:
        spec = (f"Create an AL table {obj_id} \"{name}\" with fields: "
                + "; ".join(f"{f.strip(chr(34))} ({t.strip()})" for f, t in fields[:12]) + ".")
    elif kind == "enum" and values:
        spec = (f"Create an AL enum {obj_id} \"{name}\" with values: "
                + ", ".join(v.strip('"') for v in values[:20]) + ".")
    else:
        return
    yield {"gen": "g6_spec2object",
           "messages": [{"role": "user", "content": spec},
                        {"role": "assistant", "content": _FENCE.format(obj_text.strip())}],
           "target_al": obj_text.strip(),
           "meta": {"repo": repo, "path": path, "object": f"{kind} {name}"}}


MEMBER_GENERATORS = [g1_fim, g2_sig2body, g3_explain, g5_error_fix]
