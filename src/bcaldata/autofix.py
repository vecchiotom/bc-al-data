"""Deterministic-first AL auto-fixer.

Repairs a non-compiling AL fragment so it can be used as the ``chosen`` side of a
G7 repair pair. Strategies run in order (structural -> near-name -> analyzer
code-fix), re-compiling after each applied edit until the fragment is error-clean
or no strategy makes progress (cap ``_MAX_PASSES``).

The compile used here is the same throwaway-project build as ``verify`` but with
line/column positions parsed out of the compiler output (``CompileResult``
diagnostics drop positions), because every structural fix needs the position.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from .compile_gate import compile_app

_DATA = Path.home() / "bc-al-data" / "data"
_CORPUS = _DATA / "corpus.jsonl"
_ERR_MAP = _DATA / "al_error_map.json"

_MAX_PASSES = 5

# `path(line,col): severity CODE: message`
_POS_DIAG = re.compile(
    r"^(?P<path>[^\n(]*)\((?P<line>\d+),(?P<col>\d+)\):\s+"
    r"(?P<sev>error|warning|info)\s+(?P<code>[A-Z]{2}\d{3,4}i?):\s+(?P<msg>.*)$",
    re.M,
)

_OBJECT_KEYWORDS = (
    "codeunit", "table", "page", "enum", "report", "query", "xmlport",
    "interface", "permissionset", "controladdin", "profile", "entitlement",
    "tableextension", "pageextension", "enumextension", "reportextension",
)
_WRAP_HEAD = 'codeunit 50000 "Autofix Wrapper"\n{\n'
_WRAP_OFFSET = _WRAP_HEAD.count("\n")  # body line N -> wrapped line N + offset

_AL_TRIGGERS = [
    "OnRun", "OnOpenPage", "OnClosePage", "OnQueryClosePage", "OnInit",
    "OnInsertRecord", "OnModifyRecord", "OnDeleteRecord", "OnNewRecord",
    "OnAfterGetRecord", "OnAfterGetCurrRecord", "OnFindRecord", "OnNextRecord",
    "OnInsert", "OnModify", "OnDelete", "OnRename", "OnValidate", "OnLookup",
    "OnDrillDown", "OnAssistEdit", "OnAction", "OnBeforeGetRecord",
    "OnPreDataItem", "OnPostDataItem", "OnPreReport", "OnPostReport",
    "OnInitReport", "OnPreXmlPort", "OnPostXmlPort", "OnBeforeOpen",
]
_AL_TYPES = [
    "Integer", "Decimal", "Boolean", "Text", "Code", "Date", "Time", "DateTime",
    "Duration", "Guid", "Option", "BigInteger", "Byte", "Char", "Variant",
    "Record", "RecordRef", "RecordId", "FieldRef", "KeyRef", "Blob", "Media",
    "MediaSet", "Label", "TextBuilder", "JsonObject", "JsonArray", "JsonToken",
    "JsonValue", "XmlDocument", "XmlNode", "XmlElement", "HttpClient",
    "HttpRequestMessage", "HttpResponseMessage", "HttpHeaders", "HttpContent",
    "InStream", "OutStream", "DateFormula", "Dictionary", "List", "Codeunit",
    "Enum", "Interface", "DotNet", "BigText", "Report", "Page", "Query",
]

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_QUOTED = re.compile(r'"[^"]+"')


# ---------------------------------------------------------------- vocabulary ---
_VOCAB: set[str] | None = None


def _corpus_vocab() -> set[str]:
    """Real AL identifiers mined from the local corpus, used as a near-name pool."""
    global _VOCAB
    if _VOCAB is not None:
        return _VOCAB
    v: set[str] = set()
    try:
        for line in _CORPUS.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            for key in ("member_name", "object_name"):
                if r.get(key):
                    v.add(str(r[key]).strip('"'))
            for sig in r.get("sibling_signatures") or []:
                v.update(_IDENT.findall(sig))
            v.update(_IDENT.findall(r.get("member_text") or ""))
    except OSError:
        pass
    _VOCAB = {w for w in v if len(w) >= 3}
    return _VOCAB


def _fix_strategy(code: str) -> str:
    try:
        return json.loads(_ERR_MAP.read_text()).get(code, {}).get("fix_strategy", "model")
    except OSError:
        return "model"


# ------------------------------------------------------------------ compile ---
_APP_JSON = {
    "id": "00000000-0000-4000-8000-0000000af1c0", "name": "bcaldata autofix",
    "publisher": "bcaldata", "version": "1.0.0.0", "platform": "28.0.0.0",
    "application": "28.0.0.0", "runtime": "17.0",
    "idRanges": [{"from": 50000, "to": 59999}], "features": ["NoImplicitWith"],
}
_MCP = None          # resident ALMcp — warm recompiles of the scratch project
_MCP_PROJ: Path | None = None
_MCP_DEAD = False
_MCP_LOC = re.compile(r"@(\d+):(\d+)\)")


def _needs_wrap(al: str) -> bool:
    return not al.lstrip().lower().startswith(_OBJECT_KEYWORDS)


def _scratch_project() -> Path:
    global _MCP_PROJ
    if _MCP_PROJ is None:
        from .verify import _shared_alpackages
        p = Path(tempfile.mkdtemp(prefix="bcaldata-autofix-"))
        (p / "app.json").write_text(json.dumps(_APP_JSON))
        (p / "src").mkdir()
        (p / "src" / "Snippet.al").write_text("codeunit 50000 X\n{\n}\n")
        (p / ".alpackages").symlink_to(_shared_alpackages())
        _MCP_PROJ = p
    return _MCP_PROJ


def _warm_mcp():
    """A started ALMcp with the scratch project loaded, or None if unavailable."""
    global _MCP, _MCP_DEAD
    if _MCP_DEAD:
        return None
    if _MCP is None:
        try:
            from .mcp_client import ALMcp
            import atexit
            m = ALMcp(analyzers=False).start()
            m.add_project(_scratch_project())
            atexit.register(m.close)
            _MCP = m
        except Exception:  # noqa: BLE001 - fall back to the cold compiler
            _MCP_DEAD = True
            return None
    return _MCP


def _compile(al: str, project_dir: Path | None) -> list[dict]:
    """Compile ``al``; return body-relative positioned error/warning diagnostics.

    Fragments (``project_dir is None``) recompile through a resident AL MCP server
    (warm, ~1 s); a real project falls through to the cold compiler with analyzers.
    """
    wrap = _needs_wrap(al)
    src = f"{_WRAP_HEAD}{al}\n}}\n" if wrap else al
    off = _WRAP_OFFSET if wrap else 0

    if project_dir is None:
        m = _warm_mcp()
        if m is not None:
            try:
                proj = _scratch_project()
                (proj / "src" / "Snippet.al").write_text(src)
                res = m.compile(proj)
                out = []
                for d in (res.get("diagnostics") or []) if isinstance(res, dict) else []:
                    sev = str(d.get("severity", "")).lower()
                    if sev not in ("error", "warning"):
                        continue
                    loc = _MCP_LOC.search(d.get("location", "") or "")
                    ln = int(loc.group(1)) if loc else 1
                    col = int(loc.group(2)) if loc else 1
                    out.append({"severity": sev, "code": d.get("code", ""),
                                "message": (d.get("description") or "").strip(),
                                "startLine": ln - off, "startColumn": col})
                return out
            except Exception:  # noqa: BLE001 - drop to cold path
                pass

    work = Path(tempfile.mkdtemp(prefix="bcaldata-autofix-cold-"))
    try:
        (work / "app.json").write_text(json.dumps(_APP_JSON))
        (work / "src").mkdir()
        (work / "src" / "Snippet.al").write_text(src)
        from .verify import _shared_alpackages, SYMBOL_VERSION
        (work / ".alpackages").symlink_to(_shared_alpackages())
        res = compile_app(work, SYMBOL_VERSION, analyzers=project_dir is not None)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    out = []
    for mm in _POS_DIAG.finditer(res.stdout):
        if mm["sev"] not in ("error", "warning"):
            continue
        out.append({
            "severity": mm["sev"], "code": mm["code"], "message": mm["msg"].strip(),
            "startLine": int(mm["line"]) - off, "startColumn": int(mm["col"]),
        })
    return out


def _clean(diags: list[dict]) -> bool:
    return not any(d["severity"] == "error" for d in diags)


# --------------------------------------------------------------- primitives ---
def _lines(text: str) -> list[str]:
    return text.split("\n")


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _rename_word(text: str, old: str, new: str) -> str:
    return re.sub(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])", new, text)


def _nearest(bad: str, pool: set[str]) -> str | None:
    """The single pool entry within edit distance 2 of ``bad`` (case-insensitive), else None."""
    cands = {c for c in pool
             if c != bad and 1 <= _levenshtein(bad.lower(), c.lower()) <= 2}
    by_lower: dict[str, str] = {}
    for c in cands:
        by_lower.setdefault(c.lower(), c)
    if len(by_lower) == 1:
        return next(iter(by_lower.values()))
    return None


# ------------------------------------------------------------ strategy 1: structural
def _structural(text: str, err: dict) -> str | None:
    code, ln = err["code"], err["startLine"]
    lines = _lines(text)
    if not (1 <= ln <= len(lines)):
        ln = max(1, min(len(lines), ln))
    i = ln - 1

    if code == "AL0111":  # semicolon expected
        raw = lines[i]
        body = re.sub(r"\s*//.*$", "", raw).rstrip()
        if body and not body.endswith(";"):
            lines[i] = body + ";" + raw[len(body):] if raw[len(body):].strip() == "" else body + ";"
            return "\n".join(lines)
        # statement actually ends on a previous non-blank line
        for j in range(i - 1, -1, -1):
            b = re.sub(r"\s*//.*$", "", lines[j]).rstrip()
            if b:
                if not b.endswith((";", "begin", "then", "do", "else")):
                    lines[j] = b + ";"
                    return "\n".join(lines)
                break
        return None

    if code == "AL0110":  # orphaned else — drop the ';' before it
        new = re.sub(r";(\s*)\belse\b", r"\1else", text, count=1)
        return new if new != text else None

    if code in ("AL0104", "AL0105"):
        m = re.search(r"'([^']+)' expected", err["message"])
        if code == "AL0104" and m:
            tok = m.group(1)
            if tok.lower() in ("begin", "end", ")", "(", ";", "until", "then", "do", "]", "}"):
                col = max(1, min(len(lines[i]) + 1, err["startColumn"]))
                pad = tok if tok in (")", "(", ";", "]", "}") else f"{tok} "
                lines[i] = lines[i][: col - 1] + pad + lines[i][col - 1:]
                return "\n".join(lines)
        if code == "AL0105":
            m2 = re.search(r"'([^']+)' is a keyword", err["message"])
            if m2:
                kw = m2.group(1)
                new = _rename_word(text, kw, kw + "Value")
                return new if new != text else None
        return None

    if code == "AL0791":  # unknown namespace -> drop the offending using line
        ns = re.search(r"namespace '([^']+)'", err["message"])
        target = ns.group(1) if ns else None
        keep = [ln_ for ln_ in lines
                if not (ln_.lstrip().lower().startswith("using ")
                        and (target is None or target in ln_))]
        return "\n".join(keep) if keep != lines else None

    return None


# ---------------------------------------------------- strategy 2: near-name repair
_BAD_IDENT = {
    "AL0118": r"The name '([^']+)' does not exist",
    "AL0132": r"does not contain a definition for '([^']+)'",
    "AL0134": r"'([^']+)' is not recognized as a valid type",
    "AL0162": r"'([^']+)' is not a valid trigger",
    "AL0295": r"The field '([^']+)' is not found",
    "AL0247": r"for the extension object is not found",  # name captured separately
    "AL0503": r"'([^']+)' is ambiguous",
}


def _lsp_completions(project_dir: Path, err: dict) -> set[str]:
    try:
        from .alsp import ALLanguageServer
        al_file = next(project_dir.rglob("*.al"), None)
        if al_file is None:
            return set()
        with ALLanguageServer(project_dir) as srv:
            items = srv.completion(al_file, max(0, err["startLine"] - 1),
                                   max(0, err["startColumn"] - 1))
        return {it.get("label", "").strip('"') for it in items if it.get("label")}
    except Exception:  # noqa: BLE001 - navigation LSP is best-effort here
        return set()


def _near_name(text: str, err: dict, project_dir: Path | None) -> str | None:
    code = err["code"]
    if code == "AL0247":
        m = re.search(r"target \w+ '([^']+)'", err["message"])
    else:
        pat = _BAD_IDENT.get(code)
        m = re.search(pat, err["message"]) if pat else None
    if not m:
        return None
    bad = m.group(1)

    pool: set[str] = set(_IDENT.findall(text)) | {q.strip('"') for q in _QUOTED.findall(text)}
    if code == "AL0162":
        pool = set(_AL_TRIGGERS)
    elif code == "AL0134":
        pool |= set(_AL_TYPES) | _corpus_vocab()
    else:
        pool |= _corpus_vocab()
    if project_dir is not None:
        pool |= _lsp_completions(project_dir, err)
    pool.discard(bad)

    cand = _nearest(bad, pool)
    if not cand or cand == bad:
        return None
    new = _rename_word(text, bad, cand)
    return new if new != text else None


# ------------------------------------------------ strategy 3: analyzer code-fixes
def _analyzer_fix(text: str, diags: list[dict], project_dir: Path) -> str | None:
    try:
        from .mcp_client import ALCopsMcp, alcops_mcp_command
    except Exception:  # noqa: BLE001
        return None
    if alcops_mcp_command() is None:
        return None
    al_file = next(project_dir.rglob("*.al"), None)
    if al_file is None:
        return None
    try:
        with ALCopsMcp() as cops:
            report = cops.analyze(project=project_dir)
            found = report.get("diagnostics", report) if isinstance(report, dict) else report
            for d in found or []:
                if not isinstance(d, dict) or not d.get("hasCodeFix"):
                    continue
                cops.apply_fix(project_dir, d)
            return al_file.read_text()
    except Exception:  # noqa: BLE001 - MCP server may be absent/unstable
        return None


# ------------------------------------------------------------------ entrypoint
def autofix(broken_al: str, diagnostics: list[dict],
            project_dir: Path | None = None) -> tuple[str | None, str]:
    """Repair ``broken_al`` to compile clean.

    Returns ``(fixed_al, method)`` where ``method`` is a ``+``-joined list of the
    strategies that fired, or ``(None, "unfixable:<reason>")``.

    ``diagnostics`` is the caller's first compile signal (``severity``/``code``,
    positions optional); autofix re-compiles internally for authoritative
    positions, so a loose list is fine.
    """
    project_dir = Path(project_dir) if project_dir is not None else None
    text = broken_al
    methods: list[str] = []

    diags = _compile(text, project_dir)
    for _ in range(_MAX_PASSES):
        if _clean(diags):
            if not methods:
                return text, "already-clean"
            return text, "+".join(methods)

        errors = [d for d in diags if d["severity"] == "error"]
        errors.sort(key=lambda d: (d["startLine"], d["startColumn"]))
        progressed = False

        for err in errors:
            new = _structural(text, err)
            tag = "structural"
            if new is None or new == text:
                new = _near_name(text, err, project_dir)
                tag = "near-name"
            if (new is None or new == text) and project_dir is not None:
                new = _analyzer_fix(text, diags, project_dir)
                tag = "analyzer-codefix"
            if new is not None and new != text:
                text, progressed = new, True
                methods.append(tag)
                break

        if not progressed:
            first = errors[0]["code"]
            return None, f"unfixable:{first}"
        diags = _compile(text, project_dir)

    if _clean(diags):
        return text, "+".join(methods)
    return None, f"unfixable:{[d['code'] for d in diags if d['severity'] == 'error'][:1]}"
