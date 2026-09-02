#!/usr/bin/env python3
"""Build data/al_error_map.json + summary from the reflected diagnostic catalogs.

Inputs (all produced by tools/reflect/*.cs):
  data/al_compiler_diagnostics.tsv  AL#### <tab> severity <tab> ENUM_NAME     (919 rows)
  data/al_messages.tsv              AL#### <tab> ENUM_NAME <tab> message_template
  data/analyzer_rules.tsv           id <tab> sev <tab> category <tab> enabled <tab> title <tab> msg <tab> asm
  data/alcops_rules.tsv             id <tab> cop <tab> severity <tab> category <tab> title   (union safety net)

Output:
  data/al_error_map.json            {code: record}
  data/al_error_map.summary.md      grouped table + ranked hallucination list

The judgment fields (hallucination_likelihood / fix_strategy / fix_notes /
g5_mutation / example_trigger) come from a rule-based classifier keyed off the
enum-name semantics and the message template, with a curated override table for
the codes an AL-writing LLM trips most.
"""
from __future__ import annotations
import csv, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def read_tsv(name, n):
    rows = []
    with open(DATA / name, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            parts += [""] * (n - len(parts))
            rows.append(parts[:n])
    return rows


# ---------------------------------------------------------------- load inputs
diag = {c: (sev, enum) for c, sev, enum in read_tsv("al_compiler_diagnostics.tsv", 3)}
msgs = {c: msg for c, enum, msg in read_tsv("al_messages.tsv", 3)}

SEV_MAP = {"error": "error", "warning": "warning", "info": "info",
           "hidden": "info", "": "warning"}


def norm_sev(s):
    return SEV_MAP.get(s.strip().lower(), "warning")


# ---------------------------------------------------------------- category
def category_for_enum(enum, msg):
    """AL compiler code -> category bucket from the ERR_/WRN_/INF_ name."""
    e = re.sub(r"^(ERR|WRN|INF)_", "", enum)
    el = e.lower()
    m = msg.lower()
    if re.search(r"(invalid|bad|malformed).*(literal|comment|escape|token|character)"
                 r"|unterminated|invalidmultiline|invaliddecimal|invalidint|invalidnumeric", el):
        return "lexical"
    if re.search(r"obsolete|deprecated|\bremoved\b", el):
        return "obsoletion"
    if re.search(r"permission|license|entitlement|protectionlevel|inaccessible|isnotaccessible"
                 r"|access(ibility)?modifier", el):
        return "permission"
    if re.search(r"manifest|app\.?json|appjson|package|symbol|nuget|dependency|runtimeversion"
                 r"|projectmanifest|translationapp|xliff|\.app\b|radfile|fastpublish|cache"
                 r"|directory|resourcefolder|filedoesnotexist|filenotfound|packagefile", el):
        return "metadata"
    if re.search(r"expected|syntaxerror|unexpectedtoken|orphaned|illegalstatement|illegalline"
                 r"|identifierexpectedkw|tokenexpected", el):
        return "syntax"
    if re.search(r"notfound|undeclared|undefined|namenotincontext|nosuchmember|doesnotexist"
                 r"|notdeclared|cannotresolve|unresolved|unknown(type|trigger|object|member|"
                 r"property|dotnet|method|field)|extensiontargetnotfound|appobjectnotfound"
                 r"|namespacenotfound|missingassociated|missingobjectproperty|missingproperty"
                 r"|ambigsymbol|ambigmember|ambigcall|unknownidentifier", el):
        return "binding"
    if re.search(r"typemismatch|noimplicitconversion|cannotconvert|notconvertible|badargcount"
                 r"|noover?load|ambigunary|ambigbinary|ambig|noninvocable|methodnameexpected"
                 r"|operator.*(ambiguous|applied)|wrongnumberof|incompatibletype|cannotimplicit"
                 r"|propertytypefieldtype", el):
        return "type"
    if re.search(r"duplicate|primarykey|fieldid|objectid|alreadydeclared|alreadydefined", el):
        return "metadata"
    if enum.startswith("WRN_") or enum.startswith("INF_"):
        return "semantic"
    if enum in ("None", "Void", "Unknown", ""):
        return "other"
    # every remaining ERR_ is an object-model / binding-time rule
    return "semantic"


ANALYZER_CAT = {
    "AA": "analyzer-style",           # Microsoft CodeCop
    "AW": "analyzer-correctness",     # Microsoft UICop (web-client correctness)
    "AS": "metadata",                # Microsoft AppSourceCop (breaking-change / manifest)
    "PTE": "metadata",               # Microsoft PerTenantExtensionCop
    "AC": "analyzer-correctness",     # ALCops ApplicationCop
    "DC": "analyzer-style",           # ALCops DocumentationCop
    "FC": "analyzer-style",           # ALCops FormattingCop
    "LC": "analyzer-correctness",     # ALCops LinterCop
    "PC": "analyzer-correctness",     # ALCops PlatformCop
    "TA": "analyzer-correctness",     # ALCops TestAutomationCop
}

# ---------------------------------------------------------------- curated overrides
# code -> (halluc, fix_strategy, fix_notes, g5_mutation, example_trigger)
CUR = {
 "AL0104": ("high", "deterministic", "Parser names the expected token; insert it at the caret.",
            "delete_token", "if x > 0 then\n    Message('hi')\n// missing 'end' / ';'"),
 "AL0107": ("high", "model", "Identifier slot holds a keyword or symbol; rename to a valid identifier.",
            "rename_identifier_to_keyword", "var\n    2Customer: Record Customer;"),
 "AL0105": ("high", "deterministic", "Chosen name is a reserved keyword; rename the declaration and its uses.",
            "rename_identifier_to_keyword", "var\n    Table: Record Item;"),
 "AL0109": ("high", "deterministic", "Delete or replace the stray token flagged by the parser.",
            "insert_stray_token", "Rec.Insert()();"),
 "AL0111": ("high", "deterministic", "Insert ';' at the end of the flagged statement.",
            "delete_semicolon", "Rec.Modify()\nRec.Insert();"),
 "AL0110": ("high", "deterministic", "Remove the semicolon immediately before ELSE.",
            "semicolon_before_else", "if a then\n    b();\nelse\n    c();"),
 "AL0117": ("medium", "model", "Only assignment/invocation may stand as a statement; wrap or assign the expression.",
            "bare_expression_statement", "x + 1;"),
 "AL0118": ("high", "model", "Name is unresolved: declare the variable, fix the typo, or add the using.",
            "rename_identifier", "Message(CustomerNam);"),
 "AL0122": ("high", "model", "Insert the correct conversion helper (Format, Evaluate, .AsInteger()) or fix the target type.",
            "change_var_type", "var i: Integer;\nbegin i := 'text'; end;"),
 "AL0126": ("high", "model", "Argument count disagrees with every overload; add/remove arguments to match a candidate.",
            "swap_argument_count", "Message('%1 %2', a);"),
 "AL0127": ("high", "model", "Member is a property/field, not a method; drop the parentheses.",
            "add_parens_to_property", "if Rec.Name() = '' then;"),
 "AL0125": ("medium", "deterministic", "Put a method name after '.'; usually a trailing dot typo.",
            "trailing_dot", "Rec..Insert();"),
 "AL0132": ("high", "model", "Member does not exist on that type; correct the member name or the receiver type.",
            "rename_member", "Customer.NonExistentField := 1;"),
 "AL0134": ("high", "model", "Type name is unknown; fix spelling, use the object's real name, or add the using.",
            "rename_type", "var x: Recrd Customer;"),
 "AL0162": ("high", "model", "Trigger name is not defined for this object; use a documented trigger.",
            "rename_trigger", "trigger OnAfterInsertRecord()\nbegin\nend;"),
 "AL0171": ("high", "analyzer-codefix", "Property value outside the allowed set; pick a valid value.",
            "corrupt_property_value", "SourceTable = 18;\nTableType = Bogus;"),
 "AL0172": ("medium", "model", "Unary operator not defined for that operand type; change operand or operator.",
            "operator_type_misuse", "var b: Boolean;\nbegin b := -b; end;"),
 "AL0174": ("high", "model", "Binary operator not defined for those operand types; align the types.",
            "operator_type_misuse", "var d: Date; i: Integer;\nbegin i := d * i; end;"),
 "AL0196": ("medium", "model", "Ambiguous extension method call; qualify with the declaring object.",
            "ambiguous_call", None),
 "AL0198": ("high", "model", "Variable used before it is declared in var section; add the declaration.",
            "drop_var_declaration", "begin\n    Total := 1;\nend;"),
 "AL0204": ("medium", "model", "Field types not convertible; change the field definition or use a matching type.",
            "field_type_mismatch", None),
 "AL0247": ("high", "model", "Extension target object does not exist; correct the extended object name.",
            "rename_object_ref", "tableextension 50100 X extends Custmer\n{ }"),
 "AL0266": ("medium", "model", "Return value expected/mismatched; add or fix the exit value.",
            "drop_return_value", None),
 "AL0270": ("high", "model", "Control name not present on the target page; use an existing control name.",
            "rename_control_ref", None),
 "AL0271": ("high", "model", "Action name not present on the target; use an existing action name.",
            "rename_action_ref", None),
 "AL0275": ("medium", "model", "Ambiguous symbol across extensions; fully qualify the reference.",
            "ambiguous_symbol", None),
 "AL0280": ("high", "model", "Event name not published by the target object; use a real event name.",
            "rename_event_ref", None),
 "AL0284": ("high", "model", "Event subscriber signature must match the publisher; fix the parameter types.",
            "subscriber_signature_drift", None),
 "AL0295": ("high", "model", "Field not on the target table; correct the field name.",
            "rename_field", "key(K; NoSuchField) { }"),
 "AL0313": ("high", "model", "Missing required trigger/member for this object; add it.",
            "drop_required_member", None),
 "AL0317": ("high", "deterministic", "Property declared twice in the same block; delete the duplicate.",
            "duplicate_property", "Caption = 'A';\nCaption = 'B';"),
 "AL0326": ("high", "model", "Enum value not defined on the enum; use a declared value or extend the enum.",
            "rename_enum_value", None),
 "AL0335": ("high", "model", "Method/overload not found on the target object; correct the call.",
            "rename_method_call", "Rec.CalcFild(Amount);"),
 "AL0341": ("medium", "model", "Required object property missing; add it (e.g. SourceTable, PageType).",
            "drop_required_property", None),
 "AL0383": ("high", "model", "Option value not in OptionMembers; use a declared option value.",
            "rename_option_value", None),
 "AL0432": ("low", "model", "Referenced object is marked obsolete Pending/Removed; migrate to the replacement.",
            "reference_obsolete", None),
 "AL0468": ("high", "model", "Unknown property for this element; remove it or use the correct property.",
            "rename_property", None),
 "AL0482": ("high", "model", "Accessing an implicit `with` member that no longer resolves; qualify with Rec.",
            "implicit_with_member", None),
 "AL0509": ("medium", "model", "Method exists but not accessible (scope/protection); use a public API.",
            "call_internal_method", None),
 "AL0603": ("high", "model", "Object reference (page/report/codeunit id or name) does not resolve.",
            "rename_object_ref", "RunObject = page 999999;"),
 "AL0606": ("medium", "model", "Wrong number of type arguments for the generic type.",
            "type_arg_count", None),
 "AL0651": ("low", "model", "Identifier differs only by case from the declaration; align casing.",
            "case_mismatch_identifier", None),
 "AL0791": ("high", "deterministic", "Namespace in the using directive is unknown; fix or remove the using.",
            "delete_or_corrupt_using", "using System.Fake.Namespace;"),
 "AL0796": ("medium", "model", "Type must be qualified with its namespace or a using added.",
            "drop_using_for_type", None),
 "AL1019": ("none", "none", "Compiler input/target-path configuration error, not a code defect.",
            None, None),
 "AL0468_dup": ("low", None, "", None, None),
}

# fast keyword tables -----------------------------------------------------------
HIGH_ENUM = re.compile(
    r"nosuchmember|namenotincontext|badargcount|noninvocable|methodnameexpected|unknowntype"
    r"|unknowntrigger|noimplicitconversion|fieldnotfound|eventnotfound|controlnotfound"
    r"|actionnotfound|namespacenotfound|extensiontargetnotfound|appobjectnotfound"
    r"|dataitem(orcolumn)?notfound|undefinedoptionvalue|ambigcall|ambigmember|ambigsymbol"
    r"|semicolonexpected|identifierexpected|syntaxerror|unexpectedtoken|closeparenexpected"
    r"|propertyusedasmethod|duplicateproperty|duplicatevariablename|duplicateparamname"
    r"|invalidpropertyvalue|invalidpropertyoptionvalue|invalidrunobject|unknowndotnetevent"
    r"|systemobjectnotfound|fieldgroupnotfound|viewnotfound|analysisviewnotfound"
    r"|missingassociatedproperty|noncustomizableproperty|propertynotallowed"
    r"|fieldtypemismatch|propertytypefieldtype|nametypemismatch|orphanedelse", re.I)

STRUCT_NONE = re.compile(
    r"duplicate.*id|fieldid|objectid|primarykey|manifest|package|symbol|nuget|radfile"
    r"|fastpublish|internal|analyzerdriver|emit|debugger|telemetry|licens|entitlement"
    r"|projectmanifest|translationapp|xliff|packagecache|directorynotfound|filenotfound"
    r"|resourcefolder|appfiledoesnotexist|obsoletetag|checksum", re.I)


def classify_al(code, enum, sev, cat, msg):
    if code in CUR:
        return CUR[code]
    el = enum.lower()
    # structural / config -> nobody hallucinates these into a completion
    if cat in ("metadata", "permission") or STRUCT_NONE.search(el):
        return ("none", "none", "Structural/config or environment error; not induced by prose generation.", None, None)
    if cat == "obsoletion":
        return ("low", "model", "Swap the obsolete member/object for its documented replacement.",
                "reference_obsolete", None)
    if sev == "info":
        return ("none", "none", "Informational only.", None, None)
    if cat == "lexical":
        return ("medium", "deterministic", "Rewrite the malformed literal/comment into valid lexical form.",
                "corrupt_literal", None)
    if HIGH_ENUM.search(el):
        strat = "deterministic" if cat == "syntax" else "model"
        note = ("Insert the token the parser names." if cat == "syntax"
                else "Resolve the reference against real symbols: fix the name, type, arg count, or add the using/declaration.")
        mut = {"syntax": "delete_token", "binding": "rename_identifier", "type": "rename_member"}.get(cat)
        return ("high", strat, note, mut, None)
    if cat == "syntax":
        return ("high", "deterministic", "Insert or correct the token the parser names.", "delete_token", None)
    if cat == "binding":
        return ("high", "model", "Reference does not resolve; correct the name or add the declaration/using.",
                "rename_identifier", None)
    if cat == "type":
        return ("high", "model", "Types disagree; adjust the expression, the conversion, or the declared type.",
                "change_var_type", None)
    if cat == "semantic":
        h = "medium" if sev == "error" else "low"
        return (h, "model", "Object-model rule violated; adjust the property/trigger/control to a valid configuration.",
                None, None)
    return ("low", "model", "Context-specific compiler rule; repair needs the surrounding object.", None, None)


def classify_analyzer(code, prefix, sev, title, msg):
    cat = ANALYZER_CAT.get(prefix, "analyzer-style")
    tl = (title + " " + msg).lower()
    if prefix == "AS":  # AppSource breaking-change / manifest rules
        return (cat, "none", "model",
                "Breaking-change / manifest rule; resolve by restoring compatibility or bumping the manifest.",
                None, None)
    if prefix in ("AW", "PTE"):
        return (cat, "low", "model",
                "Client/PTE capability rule; adjust the object to the supported pattern.", None, None)
    # ALCops + CodeCop style/correctness
    strat = "analyzer-codefix"
    hall = "low"
    note = "Analyzer ships a code fix; apply it (whitespace, casing, parentheses, ordering, qualification)."
    if cat == "analyzer-correctness":
        hall = "low"
        note = "Correctness lint; rewrite the flagged pattern (missing checks, wrong API, perf) per the rule text."
        strat = "analyzer-codefix" if re.search(r"parenthes|casing|qualif|order|whitespace|space|semicolon|using", tl) else "model"
    if re.search(r"space|parenthes|casing|lowercase|uppercase|begin\.\.end|blank line|indent|semicolon|sorted|suffix|prefix", tl):
        strat, hall = "analyzer-codefix", "medium"
        note = "Formatting rule with a deterministic fix (spacing, casing, parentheses, ordering)."
    mut = None
    if "parenthes" in tl:
        mut = "strip_call_parens"
    elif "space" in tl or "whitespace" in tl:
        mut = "mangle_operator_spacing"
    elif "casing" in tl or "lowercase" in tl:
        mut = "case_mismatch_keyword"
    elif "temporary" in tl and "prefix" in tl:
        mut = "drop_temp_prefix"
    elif "suffix" in tl:
        mut = "drop_label_suffix"
    return (cat, hall, strat, note, mut, None)


# ---------------------------------------------------------------- build records
records = {}

for code, (sev_raw, enum) in diag.items():
    sev = norm_sev(sev_raw)
    msg = msgs.get(code, "")
    cat = category_for_enum(enum, msg)
    hall, strat, note, mut, ex = classify_al(code, enum, sev, cat, msg)
    records[code] = {
        "code": code,
        "severity": sev,
        "enum_name": enum,
        "message_template": msg,
        "category": cat,
        "hallucination_likelihood": hall,
        "fix_strategy": strat,
        "fix_notes": note,
        "g5_mutation": mut,
        "example_trigger": ex,
    }

# analyzer rules (reflected) --------------------------------------------------
an = read_tsv("analyzer_rules.tsv", 7)
for cid, sev, acat, enabled, title, amsg, asm in an:
    m = re.match(r"^([A-Z]{2,3})\d", cid)
    if not m:
        continue
    prefix = m.group(1)
    s = norm_sev(sev)
    cat, hall, strat, note, mut, ex = classify_analyzer(cid, prefix, s, title, amsg)
    records[cid] = {
        "code": cid,
        "severity": s,
        "enum_name": "",
        "message_template": amsg or title,
        "category": cat,
        "hallucination_likelihood": hall,
        "fix_strategy": strat,
        "fix_notes": note + (f"  [{title}]" if title else ""),
        "g5_mutation": mut,
        "example_trigger": ex,
        "analyzer": asm.replace(".dll", ""),
        "enabled_by_default": enabled.lower() == "true",
    }

# union safety net: any alcops_rules.tsv id we still miss ---------------------
for row in read_tsv("alcops_rules.tsv", 5):
    cid, cop, sev, acat, title = row
    if cid == "id" or cid in records:
        continue
    m = re.match(r"^([A-Z]{2,3})\d", cid)
    prefix = m.group(1) if m else "LC"
    records[cid] = {
        "code": cid, "severity": norm_sev(sev), "enum_name": "",
        "message_template": title, "category": ANALYZER_CAT.get(prefix, "analyzer-style"),
        "hallucination_likelihood": "low", "fix_strategy": "analyzer-codefix",
        "fix_notes": f"ALCops {cop} rule; apply the analyzer fix or rewrite per the rule text.",
        "g5_mutation": None, "example_trigger": None, "analyzer": cop,
    }

out = dict(sorted(records.items()))
(DATA / "al_error_map.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- summary md
from collections import Counter, defaultdict
by_cat = defaultdict(list)
for r in out.values():
    by_cat[r["category"]].append(r)
rank = {"high": 0, "medium": 1, "low": 2, "none": 3}
halluc = sorted((r for r in out.values() if r["hallucination_likelihood"] in ("high", "medium")),
                key=lambda r: (rank[r["hallucination_likelihood"]], r["code"]))

lines = ["# AL diagnostic map — summary", "",
         f"Total codes mapped: **{len(out)}**  "
         f"({sum(1 for r in out.values() if r['code'].startswith('AL'))} AL compiler + "
         f"{sum(1 for r in out.values() if not r['code'].startswith('AL'))} analyzer rules)", "",
         "Severity: " + ", ".join(f"{k} {v}" for k, v in Counter(r['severity'] for r in out.values()).most_common()),
         "",
         "Hallucination likelihood: " + ", ".join(
             f"{k} {sum(1 for r in out.values() if r['hallucination_likelihood']==k)}"
             for k in ("high", "medium", "low", "none")),
         "", "## By category", ""]
for cat in sorted(by_cat):
    rs = by_cat[cat]
    hi = sum(1 for r in rs if r["hallucination_likelihood"] == "high")
    lines.append(f"### {cat}  ({len(rs)} codes, {hi} high-likelihood)")
    lines.append("")
    lines.append("| code | sev | enum / title | halluc | fix |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(rs, key=lambda r: r["code"]):
        label = r["enum_name"] or r["message_template"][:60]
        lines.append(f"| {r['code']} | {r['severity']} | {label} | "
                     f"{r['hallucination_likelihood']} | {r['fix_strategy']} |")
    lines.append("")

lines += ["## Ranked: codes an AL-writing LLM most commonly hits", "",
          "Drives the G5 mutation catalog and G7 auto-fix work.", "",
          "| # | code | category | template | g5_mutation | fix_strategy |",
          "|---|---|---|---|---|---|"]
for i, r in enumerate(halluc[:40], 1):
    lines.append(f"| {i} | {r['code']} | {r['category']} | {r['message_template'][:70]} | "
                 f"{r['g5_mutation'] or '—'} | {r['fix_strategy']} |")
lines.append("")
(DATA / "al_error_map.summary.md").write_text("\n".join(lines), encoding="utf-8")

print(f"wrote {len(out)} records")
print("high:", sum(1 for r in out.values() if r['hallucination_likelihood'] == 'high'))
print("medium:", sum(1 for r in out.values() if r['hallucination_likelihood'] == 'medium'))
print("templates:", sum(1 for r in out.values() if r['message_template']), "/", len(out))
