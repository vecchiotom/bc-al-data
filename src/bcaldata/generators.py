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


# ---------------- G3 model paraphrase (grounded) ----------------
_G3_SYS = ("You are an expert Microsoft Dynamics 365 Business Central AL developer. "
           "Explain the AL procedure for another developer: what it does, inputs/outputs, "
           "notable BC-specific behavior (events, IsHandled, temporary records, SetRange/SetFilter). "
           "2-4 sentences, precise, no markdown headers, do not restate the code line by line.")


def g3_paraphrase(cand: dict, llm_chat) -> dict:
    """Replace the deterministic template answer with a grounded model explanation.
    The verified facts stay in the prompt so the model cannot invent the call list."""
    facts = cand["messages"][1]["content"]
    member = cand["meta"]["member"]
    prompt = f"Verified facts: {facts}\n\n(these facts are correct — expand them into prose)"
    user_msg = cand["messages"][0]["content"]
    out = llm_chat([{"role": "system", "content": _G3_SYS},
                    {"role": "user", "content": user_msg + "\n\n" + prompt}], reasoning="low", max_tokens=350)
    new = dict(cand)
    new["messages"] = [cand["messages"][0], {"role": "assistant", "content": out.strip()}]
    new["meta"] = {**cand["meta"], "template": False, "grounded_facts": facts}
    return new


# ---------------- G4: doc-QA from the devitpro markdown ----------------
import re as _re


def g4_docqa(md_path, md_text: str) -> Iterator[dict]:
    # split on H2/H3 headings; a section becomes (question=heading, answer=body)
    for m in _re.finditer(r'^(#{2,3})\s+(.+?)\s*$', md_text, _re.M):
        start = m.end()
        nxt = _re.search(r'^#{1,3}\s', md_text[start:], _re.M)
        body = md_text[start: start + (nxt.start() if nxt else len(md_text))].strip()
        heading = m.group(2).strip()
        if len(body) < 120 or len(body) > 4000 or "```" not in body and len(body) < 200:
            continue
        if _re.search(r'\b(deprecated|removed|obsolete)\b', heading, _re.I):
            continue
        q = heading if heading.endswith("?") else f"In Business Central AL, {heading[0].lower()}{heading[1:]} — explain."
        yield {"gen": "g4_docqa",
               "messages": [{"role": "user", "content": q},
                            {"role": "assistant", "content": body}],
               "target_al": None,
               "meta": {"repo": "MicrosoftDocs/dynamics365smb-devitpro-pb",
                        "path": str(md_path), "heading": heading}}


# ---------------- G7: hard negatives from the current model ----------------
def g7_probe_prompts(rec: dict) -> list[dict] | None:
    """Prompts to sample the CURRENT model on; keep completions that FAIL compile."""
    outs = list(g1_fim(rec)) + list(g2_sig2body(rec))
    return [{"probe_of": c["gen"], "messages": [c["messages"][0]],
             "gold": c["target_al"], "meta": c["meta"]} for c in outs] or None


def g7_from_rollout(probe: dict, completion: str, compile_result) -> dict | None:
    """probe + a NON-compiling model completion + the gold correction -> preference pair."""
    if compile_result.clean:
        return None
    err_codes = sorted({c for s, c, _ in compile_result.diagnostics if s == "error"})
    klass = _classify_hallucination(err_codes, completion)
    return {"gen": "g7_hard_negative", "hallucination_class": klass,
            "messages": [probe["messages"][0], {"role": "assistant", "content": _FENCE.format(probe["gold"])}],
            "target_al": probe["gold"], "rejected_al": completion,
            "meta": {**probe["meta"], "error_codes": err_codes, "probe_of": probe["probe_of"]}}


_HALLUCINATION_CODES = {
    "AL0132": "METHOD", "AL0399": "METHOD", "AL0118": "OBJECT", "AL0128": "PARAMETER",
    "AL0137": "TRIGGER", "AL0134": "PARAMETER", "AL0185": "METHOD", "AL0432": "METHOD",
}


def _classify_hallucination(err_codes: list[str], completion: str) -> str:
    for c in err_codes:
        if c in _HALLUCINATION_CODES:
            return _HALLUCINATION_CODES[c]
    return "OTHER"


# ---------------- G8: warning -> clean (needs the Stage-2 analyzer profile) ----------------
def g8_warning_clean(rec: dict, analyzer_hits: list[tuple[str, str]], fixed_text: str | None) -> Iterator[dict]:
    """rec is a member that compiles clean but trips analyzer rule(s).
    `fixed_text` = the same member after ALCops apply_fix (or None -> review-only variant)."""
    rules = sorted({c for _, c in analyzer_hits})
    if not rules:
        return
    good = f"{rec['signature']}\n{rec['body']}"
    if fixed_text and fixed_text.strip() != good.strip():
        yield {"gen": "g8_warning_clean", "rules": rules,
               "messages": [{"role": "user",
                             "content": f"Improve this AL to satisfy the analyzers "
                                        f"({', '.join(rules)}). Keep behavior identical.\n\n{_FENCE.format(good)}"},
                            {"role": "assistant", "content": _FENCE.format(fixed_text.strip())}],
               "target_al": fixed_text.strip(), "rejected_al": good,
               "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"]}}
    # review-only: list the smells (always available)
    yield {"gen": "g8_review", "rules": rules,
           "messages": [{"role": "user", "content": f"Review this AL for code smells.\n\n{_FENCE.format(good)}"},
                        {"role": "assistant",
                         "content": "Analyzer findings: " + "; ".join(rules)
                                    + ".\nThe code compiles but violates the rules above."}],
           "target_al": None,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"], "review_only": True}}
