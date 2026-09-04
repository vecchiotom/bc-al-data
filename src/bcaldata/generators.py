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
    target = rec["member_text"]
    yield {"gen": "g1_fim",
           "messages": [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": _FENCE.format(target)}],
           "target_al": target,
           "meta": {"repo": rec["repo"], "path": rec["path"],
                    "object": f"{rec['object_kind']} {rec['object_name']}",
                    "member": rec["member_name"], "signature": rec["signature"]}}


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
    target = rec["member_text"]
    yield {"gen": "g2_sig2body",
           "messages": [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": _FENCE.format(target)}],
           "target_al": target,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                    "signature": rec["signature"]}}


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
from .mutations import CATALOG as _MUTATIONS, EXPECTED as _MUT_EXPECTED, apply_mutation as _apply_mutation


def _g5_usable(rec: dict) -> bool:
    return (rec["has_body"] and not rec["is_test"]
            and 2 <= rec["body_loc"] <= 40
            and rec["member_kind"] in ("procedure", "trigger")
            and "begin" in rec["body"])


def g5_error_fix(rec: dict) -> Iterator[dict]:
    if not _g5_usable(rec):
        return
    good = rec["member_text"]
    obj_ctx = {"object_kind": rec["object_kind"], "object_name": rec["object_name"],
               "object_head": rec["object_head"]}
    for mid, fn in _MUTATIONS:
        try:
            res = _apply_mutation(mid, fn, rec, obj_ctx)
        except Exception:  # noqa: BLE001 - a mutation that trips on odd source is simply skipped
            continue
        if res is None:
            continue
        bad, desc, codes = res
        yield {"gen": "g5_error_fix", "mutation": mid,
               "messages": [{"role": "user",
                             "content": f"This AL does not compile. Fix it.\n\n{_FENCE.format(bad)}"},
                            {"role": "assistant", "content": _FENCE.format(good)}],
               "target_al": good, "rejected_al": bad,
               "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                        "signature": rec["signature"], "mutation_desc": desc,
                        "expected_diagnostic": _MUT_EXPECTED.get(mid, codes)}}


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
           "Write 2-4 complete sentences as a single paragraph, then stop. Do not repeat yourself, "
           "do not add markdown headers, do not restate the code line by line. "
           "Use only method and type names that appear in the code or the verified facts.")


def _dedupe_para(text: str) -> str:
    """Keep the first paragraph and drop any later paragraph that repeats it.

    The local model occasionally emits the same explanation twice; a verbatim or
    prefix-duplicate trailing block is noise, not content."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if not blocks:
        return text
    kept = [blocks[0]]
    for b in blocks[1:]:
        if any(b.startswith(k[:40]) or k.startswith(b[:40]) for k in kept):
            break
        kept.append(b)
    return "\n\n".join(kept)


def g3_paraphrase(cand: dict, llm_chat) -> dict:
    """Replace the deterministic template answer with a grounded model explanation.
    The verified facts stay in the prompt so the model cannot invent the call list."""
    facts = cand["messages"][1]["content"]
    member = cand["meta"]["member"]
    prompt = f"Verified facts: {facts}\n\n(these facts are correct — expand them into prose)"
    user_msg = cand["messages"][0]["content"]
    out = llm_chat([{"role": "system", "content": _G3_SYS},
                    {"role": "user", "content": user_msg + "\n\n" + prompt}],
                   reasoning="low", temperature=0.3, max_tokens=512)
    new = dict(cand)
    new["messages"] = [cand["messages"][0], {"role": "assistant", "content": _dedupe_para(out.strip())}]
    new["meta"] = {**cand["meta"], "template": False, "grounded_facts": facts}
    return new


# ---------------- G4: doc-QA from the devitpro markdown ----------------
_G4_REPO = "MicrosoftDocs/dynamics365smb-devitpro-pb"

# Only the AL language surface teaches syntax; ITpro/admin trees are dropped wholesale.
_G4_KEEP_SECTION = "developer"
_G4_DROP_PATH = re.compile(
    r'(?:^|/)(?:administration|deployment|upgrade|analyzers|avs-diagnostics|diagnostics'
    r'|readiness|includes)/|telemetry|monitor', re.I)

# Navigational / generic headings that carry no concept on their own.
_G4_DENY_HEADINGS = frozenset({
    "see also", "see", "related information", "related links", "related content",
    "next steps", "prerequisites", "in this article", "overview", "introduction",
    "feedback", "remarks", "example", "examples", "syntax", "tip", "note", "caution",
    "important", "references", "additional resources", "more information", "requirements",
    "description", "applies to", "further information", "reason for the rule",
    "bad code example", "good code example", "how to fix it", "how to fix this diagnostic",
})

_G4_REF_KIND = {
    "method": "How do I use the `{name}` method in Business Central AL? What does it do?",
    "property": "What does the `{name}` property do in Business Central AL, and how do I set it?",
    "trigger": "What is the `{name}` trigger in Business Central AL and when does it run?",
    "attribute": "What does the `{name}` attribute do in Business Central AL?",
    "data type": "What is the `{name}` data type in Business Central AL and how do I use it?",
    "keyword": "What does the `{name}` keyword do in Business Central AL?",
}
_G4_H1_REF = re.compile(
    r'^(?P<name>.+?)\s*(?:\([^)]*\))?\s+(?P<kind>Method|Property|Trigger|Attribute|Data Type|Keyword)\s*$',
    re.I)
_G4_FENCE = re.compile(r'^```')
_G4_AL_FENCE = re.compile(r'^```\s*(al|c#|csharp|pascal)\b', re.I)
_G4_LINK_LINE = re.compile(r'^[-*>\s]*\[[^\]]+\]\([^)]+\)[.\s]*$')
_G4_NOISE_LINE = re.compile(r'^(\||!\[|\[//\]|\[!INCLUDE|\[!NOTE|\[!TIP|\[!IMPORTANT|&emsp;|<)')


def _g4_front_title(md_text: str) -> str | None:
    """`title:` from a leading YAML front-matter block, if present."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', md_text, re.S)
    if not m:
        return None
    t = re.search(r'^title:\s*(.+?)\s*$', m.group(1), re.M)
    return t.group(1).strip().strip('"\'') if t else None


def _g4_clean_heading(h: str) -> str:
    return re.sub(r'\s*[\[(](?:AL|NAV|Windows|On-Prem[^)\]]*)[\])]\s*$', '', h).strip()


def _g4_strip_code(body: str) -> str:
    return re.sub(r'```.*?```', ' ', body, flags=re.S)


def _g4_sentences(prose: str) -> int:
    return len(re.findall(r'[.!?](?:\s|$)', prose))


def _g4_prose_ratio(body: str) -> float:
    """Fraction of non-code lines that read as prose rather than link lists,
    table rows, image tags, or doc-generator comment markers."""
    prose = total = 0
    in_fence = False
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _G4_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        total += 1
        if _G4_LINK_LINE.match(line) or _G4_NOISE_LINE.match(line):
            continue
        prose += 1
    return prose / total if total else 0.0


def _g4_body_ok(body: str) -> bool:
    """A section body worth keeping: enough real prose, and either two sentences
    of it or a fenced AL/C#/Pascal code block."""
    if not (150 <= len(body) <= 6000):
        return False
    prose = _g4_strip_code(body)
    prose_chars = len(re.sub(r'\[[^\]]+\]\([^)]+\)|[|>*#`_-]', '', prose).strip())
    if prose_chars < 150:
        return False
    has_al = any(_G4_AL_FENCE.match(l.strip()) for l in body.splitlines())
    if _g4_prose_ratio(body) < 0.60 and not has_al:
        return False
    return has_al or _g4_sentences(prose) >= 2


def _g4_reference(md_text: str, front_title: str | None) -> tuple[str, str] | None:
    """`(name, kind)` when the page documents one AL method/property/trigger/type,
    detected from the H1 or the front-matter title plus a `## Syntax` section."""
    h1 = re.search(r'^#\s+(.+?)\s*$', md_text, re.M)
    for text in (h1.group(1) if h1 else None, front_title):
        if not text:
            continue
        m = _G4_H1_REF.match(text.strip())
        if m:
            kind = m.group("kind").lower()
            name = re.sub(r'\s*\([^)]*\)\s*$', '', m.group("name")).strip()
            if name and re.fullmatch(r'[\w.:\[\], ]+', name):
                return name, kind
    return None


def _g4_reference_body(md_text: str) -> str:
    """The teaching part of a reference page: everything after the H1 up to the
    first navigational section, with doc-generator markers removed."""
    after = re.split(r'^#\s+.+?\s*$', md_text, maxsplit=1, flags=re.M)[-1]
    after = re.split(r'^##\s+(?:Related information|See also)\s*$', after, maxsplit=1, flags=re.M)[0]
    after = re.sub(r'^\[//\]: #.*$\n?', '', after, flags=re.M)
    after = re.sub(r'^>\s*\*\*Version\*\*:.*$\n?', '', after, flags=re.M)
    return after.strip()


def g4_docqa(md_path, md_text: str) -> Iterator[dict]:
    """Turn one devitpro markdown page into doc-QA pairs.

    Only pages under `dev-itpro/developer/` are used; ITpro, admin, upgrade, and
    telemetry trees carry no AL syntax. Reference pages (method/property/trigger/
    type) yield one pair keyed by the member name; other pages yield one pair per
    concept H2/H3 section that survives the prose and heading filters.
    """
    parts = str(md_path).replace("\\", "/").split("/")
    section = parts[1] if len(parts) > 1 else parts[0]
    if section != _G4_KEEP_SECTION or _G4_DROP_PATH.search(str(md_path)):
        return
    meta = {"repo": _G4_REPO, "path": str(md_path), "doc_section": section}
    front_title = _g4_front_title(md_text)

    ref = _g4_reference(md_text, front_title)
    if ref:
        name, kind = ref
        body = _g4_reference_body(md_text)
        if _g4_body_ok(body) and not re.search(r'\b(deprecated|obsolete|removed)\b', body[:400], re.I):
            q = _G4_REF_KIND.get(kind, _G4_REF_KIND["method"]).format(name=name)
            yield {"gen": "g4_docqa",
                   "messages": [{"role": "user", "content": q},
                                {"role": "assistant", "content": body}],
                   "target_al": None,
                   "meta": {**meta, "heading": f"{name} {kind.title()}"}}
        return

    for m in re.finditer(r'^(#{2,3})\s+(.+?)\s*$', md_text, re.M):
        start = m.end()
        nxt = re.search(r'^#{1,3}\s', md_text[start:], re.M)
        body = md_text[start: start + (nxt.start() if nxt else len(md_text))].strip()
        heading = _g4_clean_heading(m.group(2))
        norm = re.sub(r'[?:.\s]+$', '', heading).lower()
        if not norm or norm in _G4_DENY_HEADINGS:
            continue
        if re.search(r'\b(deprecated|removed|obsolete)\b', heading, re.I):
            continue
        if not _g4_body_ok(body):
            continue
        q = heading if heading.endswith("?") else f"In Business Central AL, explain {heading}."
        yield {"gen": "g4_docqa",
               "messages": [{"role": "user", "content": q},
                            {"role": "assistant", "content": body}],
               "target_al": None,
               "meta": {**meta, "heading": heading}}


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


# ---------------- G8: analyzer warning -> clean AL ----------------
# rec carries `analyzer_hits` (from Task A: [[code, severity, line], ...]). The fixed
# text comes from ALCops MCP `apply_fix` (see generate_g8.fix_member); this module
# only shapes the training rows.


def _g8_member_al(rec: dict) -> str:
    return f"{rec['signature']}\n{rec['body']}"


def _g8_rules(rec: dict) -> list[str]:
    return sorted({h[0] for h in (rec.get("analyzer_hits") or [])})


def g8_warning_clean(rec: dict, fixed_text: str | None = None,
                     applied_rules: list[str] | None = None) -> Iterator[dict]:
    """SFT + preference pair: the member as written -> the analyzer-clean member.

    `fixed_text` is the member text after one or more ALCops `apply_fix` passes; a
    row is emitted only when a fix actually changed the code. Downstream `verify`
    still compiles `target_al`."""
    rules = _g8_rules(rec)
    if not rules or not fixed_text:
        return
    good = _g8_member_al(rec)
    if fixed_text.strip() == good.strip():
        return
    applied = sorted(applied_rules) if applied_rules else rules
    yield {"gen": "g8_warning_clean", "rules": applied,
           "messages": [{"role": "user",
                         "content": f"Improve this AL to satisfy the analyzers "
                                    f"({', '.join(applied)}). Keep behavior identical.\n\n{_FENCE.format(good)}"},
                        {"role": "assistant", "content": _FENCE.format(fixed_text.strip())}],
           "target_al": fixed_text.strip(), "rejected_al": good,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                    "object": f"{rec['object_kind']} {rec['object_name']}",
                    "analyzer_hits": rec.get("analyzer_hits") or []}}


def g8_review(rec: dict, message_templates: dict[str, str] | None = None) -> Iterator[dict]:
    """Review variant: given the member, name the analyzer findings and one line
    per rule from `al_error_map.json`'s `message_template`. Always available for a
    member with `analyzer_hits` — no fix required."""
    rules = _g8_rules(rec)
    if not rules:
        return
    good = _g8_member_al(rec)
    templates = message_templates or {}
    lines = [f"- {r}: {templates[r]}" if templates.get(r) else f"- {r}" for r in rules]
    answer = ("Analyzer findings: " + ", ".join(rules) + ".\n" + "\n".join(lines)
              + "\nThe code compiles but violates the rules above.")
    yield {"gen": "g8_review", "rules": rules,
           "messages": [{"role": "user",
                         "content": f"Review this AL for code smells.\n\n{_FENCE.format(good)}"},
                        {"role": "assistant", "content": answer}],
           "target_al": None,
           "meta": {"repo": rec["repo"], "path": rec["path"], "member": rec["member_name"],
                    "object": f"{rec['object_kind']} {rec['object_name']}",
                    "analyzer_hits": rec.get("analyzer_hits") or [], "review_only": True}}
