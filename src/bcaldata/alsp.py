"""Resident AL Language Server client (stdio, LSP `Content-Length` framing).

`al launchlspserver <project-dirs...> --packagecachepath <dir> [--assemblyprobingpaths ...]
[--codeanalyzers ...]` speaks JSON-RPC 2.0 over stdio with `Content-Length`
framing. The `[AL LSP] ...` banner and the 24-endpoint registration list go to
**stderr**, not stdout, so the stdout reader sees only clean LSP frames; it still
skips any non-header line defensively.

Verified server capabilities (BC 28 / al v18.0.40): hover, definition,
completion, documentSymbol, references, rename, formatting, folding, signature
help, workspace/symbol. **The agentic AL LSP does not do diagnostics** — it
advertises no `diagnosticProvider`, never sends `textDocument/publishDiagnostics`,
and ignores `textDocument/diagnostic` / `workspace/diagnostic` requests (probed
with real syntax errors, `didSave`, and `didChange`). Error/analyzer verdicts
therefore come from the AL MCP compiler: `ALLanguageServer.diagnostics()` lazily
starts a co-resident `ALMcp` on the same project and returns its compile
diagnostics. Navigation stays on LSP (0.3 s init, warm thereafter).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

AL_BIN = os.environ.get("AL_BIN", str(Path.home() / ".dotnet/tools/al"))
_DOTNET_ROOT = os.environ.get("DOTNET_ROOT", str(Path.home() / ".dotnet"))

_DEFAULT_TIMEOUT = 90.0
_DEBUG = bool(os.environ.get("BCALDATA_ALSP_DEBUG"))


def _dbg(*a: object) -> None:
    if _DEBUG:
        print("[alsp]", *a, flush=True)


def _shared_package_cache() -> Path:
    """The 28.0 symbol set seeded once by `verify._shared_alpackages()`."""
    from .verify import _shared_alpackages

    return _shared_alpackages()


def _analyzer_dlls() -> list[str]:
    """The 7 ALCops DLLs plus Microsoft CodeCop, matching `compile_gate._analyzer_args`."""
    out: list[str] = []
    alcops = os.environ.get("ALCOPS_DIR")
    if alcops:
        d = Path(alcops)
        for name in ("Common", "LinterCop", "PlatformCop", "FormattingCop",
                     "ApplicationCop", "DocumentationCop", "TestAutomationCop"):
            p = d / f"ALCops.{name}.dll"
            if p.is_file():
                out.append(str(p))
    comp = os.environ.get("AL_COMPILER_DIR")
    if comp:
        cc = Path(comp) / "Microsoft.Dynamics.Nav.CodeCop.dll"
        if cc.is_file():
            out.append(str(cc))
    return out


class ALLSPError(RuntimeError):
    """LSP request failed, timed out, or the server exited."""


class ALLanguageServer:
    """One resident `al launchlspserver` process for a single project directory.

    Not thread-safe: drive one instance from one worker. `close()` is idempotent.
    """

    def __init__(self, project_dir: str | Path, *,
                 package_cache: str | Path | None = None,
                 analyzers: bool = True,
                 timeout: float = _DEFAULT_TIMEOUT) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.package_cache = Path(package_cache) if package_cache else _shared_package_cache()
        self.timeout = timeout
        self._analyzers = analyzers
        self._proc: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._lock = threading.Lock()
        self._responses: dict[int, object] = {}
        self._resp_event = threading.Event()
        self._diagnostics: dict[str, list[dict]] = {}
        self._diag_versions: dict[str, int] = {}
        self._diag_cv = threading.Condition()
        self._reader: threading.Thread | None = None
        self._stderr_drain: threading.Thread | None = None
        self._alive = False
        self._doc_versions: dict[str, int] = {}
        self._mcp: object | None = None  # lazily started ALMcp for diagnostics()

    # ---- process lifecycle -------------------------------------------------

    def start(self) -> "ALLanguageServer":
        if self._proc is not None:
            return self
        args = [AL_BIN, "launchlspserver", str(self.project_dir), "--nolog",
                "--packagecachepath", str(self.package_cache)]
        root = _artifact_platform_dir()
        if root:
            args += ["--assemblyprobingpaths", root]
        if self._analyzers:
            dlls = _analyzer_dlls()
            if dlls:
                args += ["--codeanalyzers", ",".join(dlls)]
        env = {**os.environ, "DOTNET_ROOT": _DOTNET_ROOT}
        self._proc = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, bufsize=0, cwd=str(self.project_dir),
        )
        self._alive = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._stderr_drain = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_drain.start()
        self.initialize()
        return self

    def __enter__(self) -> "ALLanguageServer":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        mcp, self._mcp = self._mcp, None
        if mcp is not None:
            try:
                mcp.close()
            except Exception:  # noqa: BLE001
                pass
        p = self._proc
        if p is None:
            return
        try:
            if p.poll() is None:
                try:
                    self._request("shutdown", None, timeout=10)
                    self._notify("exit", None)
                except Exception:  # noqa: BLE001 - shutting down regardless
                    pass
            self._alive = False
            self._proc = None
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=5)
        finally:
            for stream in (p.stdin, p.stdout, p.stderr):
                try:
                    stream and stream.close()
                except Exception:  # noqa: BLE001
                    pass

    # ---- framing ---------------------------------------------------------

    def _send(self, msg: dict) -> None:
        if not self._proc or not self._proc.stdin:
            raise ALLSPError("server not running")
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        _dbg("send:", str(msg)[:160])
        try:
            self._proc.stdin.write(header + body)
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise ALLSPError(f"write to LSP server failed: {e}") from e

    def _read_loop(self) -> None:
        """Skip the banner, then parse `Content-Length` frames until stdout closes."""
        out = self._proc.stdout if self._proc else None
        if out is None:
            return
        try:
            while self._alive:
                line = out.readline()
                if not line:
                    break
                low = line.lower()
                if not low.startswith(b"content-length:"):
                    _dbg("skip line:", line[:120])
                    continue  # `[AL LSP] ...` banner or a stray blank line
                length = int(line.split(b":", 1)[1].strip())
                # consume remaining headers up to the blank separator line
                while True:
                    h = out.readline()
                    if not h or h in (b"\r\n", b"\n"):
                        break
                payload = b""
                while len(payload) < length:
                    chunk = out.read(length - len(payload))
                    if not chunk:
                        break
                    payload += chunk
                try:
                    msg = json.loads(payload.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                _dbg("recv:", str(msg)[:200])
                self._dispatch(msg)
        finally:
            self._alive = False
            with self._diag_cv:
                self._diag_cv.notify_all()
            self._resp_event.set()

    def _drain_stderr(self) -> None:
        err = self._proc.stderr if self._proc else None
        if err is None:
            return
        try:
            for ln in iter(err.readline, b""):
                _dbg("stderr:", ln[:200])
                if not self._alive:
                    break
        except Exception:  # noqa: BLE001 - diagnostic stream only
            pass

    def _dispatch(self, msg: dict) -> None:
        if "id" in msg and ("result" in msg or "error" in msg):
            with self._lock:
                self._responses[msg["id"]] = msg
            self._resp_event.set()
            return
        method = msg.get("method")
        if method == "textDocument/publishDiagnostics":
            params = msg.get("params", {})
            uri = params.get("uri", "")
            with self._diag_cv:
                self._diagnostics[uri] = params.get("diagnostics", [])
                self._diag_versions[uri] = params.get("version", self._diag_versions.get(uri, 0) + 1)
                self._diag_cv.notify_all()
            return
        if "id" in msg:
            # server-to-client request (e.g. workspace/configuration); answer minimally
            self._reply(msg["id"], None if msg.get("method") != "workspace/configuration"
                        else [{} for _ in msg.get("params", {}).get("items", [])])

    # ---- JSON-RPC ------------------------------------------------------

    def _reply(self, req_id: object, result: object) -> None:
        try:
            self._send({"jsonrpc": "2.0", "id": req_id, "result": result})
        except ALLSPError:
            pass

    def _notify(self, method: str, params: object) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _request(self, method: str, params: object, *, timeout: float | None = None) -> object:
        timeout = self.timeout if timeout is None else timeout
        with self._lock:
            rid = self._next_id
            self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if rid in self._responses:
                    msg = self._responses.pop(rid)
                    break
            if not self._alive:
                raise ALLSPError(f"server exited before responding to {method}")
            self._resp_event.wait(0.2)
            self._resp_event.clear()
        else:
            raise ALLSPError(f"timeout after {timeout}s waiting for {method}")
        if isinstance(msg, dict) and msg.get("error"):
            raise ALLSPError(f"{method} failed: {msg['error']}")
        return msg.get("result") if isinstance(msg, dict) else None

    # ---- handshake ---------------------------------------------------

    def initialize(self) -> object:
        params = {
            "processId": os.getpid(),
            "clientInfo": {"name": "bcaldata-alsp", "version": "1"},
            "rootUri": self.project_dir.as_uri(),
            "workspaceFolders": [{"uri": self.project_dir.as_uri(), "name": self.project_dir.name}],
            "capabilities": {
                "textDocument": {
                    "publishDiagnostics": {"relatedInformation": True, "versionSupport": True},
                    "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                    "hover": {"contentFormat": ["plaintext", "markdown"]},
                    "synchronization": {"didSave": True, "dynamicRegistration": False},
                },
                "workspace": {"configuration": True, "workspaceFolders": True},
            },
        }
        result = self._request("initialize", params, timeout=self.timeout)
        self._notify("initialized", {})
        return result

    # ---- documents -------------------------------------------------

    def _uri(self, file_path: str | Path) -> str:
        return Path(file_path).resolve().as_uri()

    def open_document(self, file_path: str | Path, text: str) -> str:
        uri = self._uri(file_path)
        version = self._doc_versions.get(uri, 0) + 1
        self._doc_versions[uri] = version
        if version == 1:
            self._notify("textDocument/didOpen", {"textDocument": {
                "uri": uri, "languageId": "al", "version": version, "text": text}})
        else:
            self._notify("textDocument/didChange", {
                "textDocument": {"uri": uri, "version": version},
                "contentChanges": [{"text": text}]})
        return uri

    def close_document(self, file_path: str | Path) -> None:
        uri = self._uri(file_path)
        if uri in self._doc_versions:
            self._notify("textDocument/didClose", {"textDocument": {"uri": uri}})
            self._doc_versions.pop(uri, None)

    # ---- public API ----------------------------------------------

    def _mcp_server(self) -> object:
        if self._mcp is None:
            from .mcp_client import ALMcp

            self._mcp = ALMcp(projects=[self.project_dir],
                              package_cache=self.package_cache,
                              analyzers=self._analyzers,
                              timeout=max(self.timeout, 240)).start()
        return self._mcp

    def diagnostics(self, file_path: str | Path, text: str, *,
                    timeout: float | None = None) -> list[dict]:
        """Write `text` to `file_path` (must be inside this server's project),
        compile the project through the co-resident AL MCP server, and return
        `[{severity, code, message, range}]`.

        `severity` is the LSP integer 1..4 (1=error, 2=warning, 3=info, 4=hint).

        The agentic AL LSP has no diagnostics channel (see module docstring), so
        this delegates to `ALMcp.al_compile`; the MCP process keeps the symbol
        set and JIT warm, which is the speedup the verify stage needs.
        """
        path = Path(file_path).resolve()
        try:
            path.relative_to(self.project_dir)
        except ValueError:
            raise ALLSPError(f"{path} is not inside project {self.project_dir}") from None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        mcp = self._mcp_server()
        res = mcp.compile(self.project_dir, enable_code_analysis=self._analyzers,
                          only_errors=False, timeout=timeout)
        raw = res.get("diagnostics", []) if isinstance(res, dict) else []
        this_file = path.name
        out: list[dict] = []
        for d in raw:
            if not isinstance(d, dict):
                continue
            df = _diag_file(d)
            if df and Path(df).name != this_file:
                continue
            out.append({
                "severity": _sev_int(d.get("severity")),
                "code": _code_str(d.get("code") or d.get("id") or d.get("ruleId")),
                "message": d.get("message") or d.get("description") or "",
                "range": _diag_range(d),
            })
        return out

    def error_codes(self, file_path: str | Path, text: str, **kw: object) -> set[str]:
        return {d["code"] for d in self.diagnostics(file_path, text, **kw)
                if d["severity"] == 1 and d["code"]}

    def is_error_clean(self, file_path: str | Path, text: str, **kw: object) -> bool:
        return not any(d["severity"] == 1 for d in self.diagnostics(file_path, text, **kw))

    def document_symbols(self, file_path: str | Path, text: str | None = None) -> list[dict]:
        if text is not None:
            self.open_document(file_path, text)
        return self._request("textDocument/documentSymbol",
                             {"textDocument": {"uri": self._uri(file_path)}}) or []

    def hover(self, file_path: str | Path, line: int, char: int) -> str:
        res = self._request("textDocument/hover", {
            "textDocument": {"uri": self._uri(file_path)},
            "position": {"line": line, "character": char}})
        if not res:
            return ""
        contents = res.get("contents")
        if isinstance(contents, dict):
            return contents.get("value", "")
        if isinstance(contents, list):
            return "\n".join(c.get("value", c) if isinstance(c, dict) else str(c) for c in contents)
        return str(contents or "")

    def definition(self, file_path: str | Path, line: int, char: int) -> list[dict]:
        res = self._request("textDocument/definition", {
            "textDocument": {"uri": self._uri(file_path)},
            "position": {"line": line, "character": char}})
        if not res:
            return []
        return res if isinstance(res, list) else [res]

    def completion(self, file_path: str | Path, line: int, char: int) -> list[dict]:
        res = self._request("textDocument/completion", {
            "textDocument": {"uri": self._uri(file_path)},
            "position": {"line": line, "character": char}})
        if isinstance(res, dict):
            return res.get("items", [])
        return res or []


def _code_str(code: object) -> str:
    if isinstance(code, dict):
        return str(code.get("value", ""))
    return "" if code is None else str(code)


_SEV_NAMES = {"error": 1, "warning": 2, "info": 3, "information": 3, "hint": 4, "hidden": 4}


def _sev_int(sev: object) -> int | None:
    if isinstance(sev, int):
        return sev
    if isinstance(sev, str):
        return _SEV_NAMES.get(sev.strip().lower())
    return None


_LOCATION_RE = re.compile(r"(?:SourceFile\()?([^()@]+?)(?:@(\d+):(\d+))?\)?$")


def _diag_file(d: dict) -> str:
    direct = d.get("file") or d.get("filePath") or d.get("documentPath")
    if direct:
        return str(direct)
    loc = d.get("location")
    if isinstance(loc, str):
        m = _LOCATION_RE.search(loc.strip())
        if m:
            return m.group(1).strip()
    if isinstance(loc, dict):
        return str(loc.get("uri") or loc.get("file") or "")
    return ""


def _diag_range(d: dict) -> dict | None:
    if isinstance(d.get("range"), dict):
        return d["range"]
    line = d.get("line", d.get("startLine"))
    col = d.get("column", d.get("startColumn", d.get("character")))
    if line is None and isinstance(d.get("location"), str):
        m = _LOCATION_RE.search(d["location"].strip())
        if m and m.group(2):
            line, col = int(m.group(2)), int(m.group(3))
    if line is None:
        return None
    line = int(line)
    start = {"line": line - 1 if line > 0 else 0, "character": int(col) if col is not None else 0}
    return {"start": start, "end": dict(start)}


def _artifact_platform_dir() -> str | None:
    from .compile_gate import artifact_root

    sv = os.environ.get("BC_VERSION", "28.0")
    mm = ".".join(sv.split(".")[:2])
    root = artifact_root(mm)
    if root is None:
        return None
    plat = root / "platform"
    return str(plat) if plat.is_dir() else None
