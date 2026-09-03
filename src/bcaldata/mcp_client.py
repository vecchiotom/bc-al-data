"""Stdio MCP clients: the AL MCP server (`al launchmcpserver`) and ALCops MCP.

Both speak MCP (JSON-RPC 2.0) over stdio. The AL server frames with LSP-style
`Content-Length` headers; the ALCops server (when built) uses newline-delimited
JSON. `MCPClient` autodetects: it tries a `Content-Length` frame first and falls
back to a bare `\\n`-terminated line if the first bytes back are not an LSP header.

`ALMcp` wraps the AL server's compile/diagnostic tools; `ALCopsMcp` wraps the
analyzer fix tools. `ALCopsMcp.apply_fix` is what G8 needs: analyzer hit ->
fixed file text.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

AL_BIN = os.environ.get("AL_BIN", str(Path.home() / ".dotnet/tools/al"))
_DOTNET_ROOT = os.environ.get("DOTNET_ROOT", str(Path.home() / ".dotnet"))
_PROTOCOL_VERSION = "2024-11-05"
_DEBUG = bool(os.environ.get("BCALDATA_MCP_DEBUG"))


def _dbg(*a: object) -> None:
    if _DEBUG:
        print("[mcp]", *a, flush=True)


class MCPError(RuntimeError):
    """MCP request failed, timed out, or the server exited."""


class MCPClient:
    """JSON-RPC 2.0 over stdio with `Content-Length` or newline framing (autodetected)."""

    def __init__(self, args: list[str], *, env: dict | None = None,
                 cwd: str | Path | None = None, timeout: float = 120.0,
                 name: str = "mcp") -> None:
        self._args = args
        self._env = {**os.environ, "DOTNET_ROOT": _DOTNET_ROOT, **(env or {})}
        self._cwd = str(cwd) if cwd else None
        self.timeout = timeout
        self.name = name
        self._proc: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._lock = threading.Lock()
        self._responses: dict[int, dict] = {}
        self._event = threading.Event()
        # MCP's stdio transport is newline-delimited JSON; a few servers use
        # LSP-style `Content-Length` headers. Start on the spec default and let
        # the reader switch if the first frame back proves otherwise.
        self._framing: str = "line"  # "header" | "line"
        self._alive = False
        self._reader: threading.Thread | None = None
        self._stderr_tail: list[bytes] = []
        self.server_info: dict = {}
        self.tools: list[dict] = []

    # ---- lifecycle -----------------------------------------------------

    def start(self) -> "MCPClient":
        if self._proc is not None:
            return self
        self._proc = subprocess.Popen(
            self._args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=self._env, cwd=self._cwd, bufsize=0,
        )
        self._alive = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        self._handshake()
        return self

    def __enter__(self) -> "MCPClient":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        p, self._proc = self._proc, None
        if p is None:
            return
        self._alive = False
        try:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=5)
        finally:
            for s in (p.stdin, p.stdout, p.stderr):
                try:
                    s and s.close()
                except Exception:  # noqa: BLE001
                    pass

    # ---- framing ------------------------------------------------------

    def _write(self, msg: dict) -> None:
        if not self._proc or not self._proc.stdin:
            raise MCPError(f"{self.name}: server not running")
        body = json.dumps(msg).encode("utf-8")
        if self._framing == "line":
            data = body + b"\n"
        else:  # default to header framing until the first reply proves otherwise
            data = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
        _dbg("send", self._framing, str(msg)[:200])
        try:
            self._proc.stdin.write(data)
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise MCPError(f"{self.name}: write failed: {e}") from e

    def _read_loop(self) -> None:
        out = self._proc.stdout if self._proc else None
        if out is None:
            return
        try:
            while self._alive:
                line = out.readline()
                if not line:
                    break
                stripped = line.strip()
                _dbg("raw", line[:200])
                if not stripped:
                    continue
                if stripped.lower().startswith(b"content-length:"):
                    self._framing = "header"
                    length = int(stripped.split(b":", 1)[1].strip())
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
                else:
                    if stripped[:1] not in (b"{", b"["):
                        continue  # banner / log noise on a line-framed stream
                    self._framing = "line"
                    payload = stripped
                try:
                    self._dispatch(json.loads(payload.decode("utf-8")))
                except json.JSONDecodeError:
                    continue
        finally:
            self._alive = False
            self._event.set()

    def _drain_stderr(self) -> None:
        err = self._proc.stderr if self._proc else None
        if err is None:
            return
        try:
            for ln in iter(err.readline, b""):
                _dbg("stderr", ln[:200])
                self._stderr_tail.append(ln)
                del self._stderr_tail[:-40]
                if not self._alive:
                    break
        except Exception:  # noqa: BLE001
            pass

    def _dispatch(self, msg: dict) -> None:
        if "id" in msg and ("result" in msg or "error" in msg):
            with self._lock:
                self._responses[msg["id"]] = msg
            self._event.set()
        elif "id" in msg and "method" in msg:
            self._write({"jsonrpc": "2.0", "id": msg["id"], "result": {}})

    # ---- JSON-RPC ----------------------------------------------------

    def _notify(self, method: str, params: object = None) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def request(self, method: str, params: object = None, *, timeout: float | None = None) -> dict:
        timeout = self.timeout if timeout is None else timeout
        with self._lock:
            rid = self._next_id
            self._next_id += 1
        self._write({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if rid in self._responses:
                    msg = self._responses.pop(rid)
                    break
            if not self._alive:
                tail = b"".join(self._stderr_tail[-10:]).decode("utf-8", "replace")
                raise MCPError(f"{self.name}: server exited before responding to {method}\n{tail}")
            self._event.wait(0.2)
            self._event.clear()
        else:
            raise MCPError(f"{self.name}: timeout after {timeout}s on {method}")
        if msg.get("error"):
            raise MCPError(f"{self.name}: {method} failed: {msg['error']}")
        return msg.get("result", {})

    # ---- MCP -------------------------------------------------------

    def _handshake(self) -> None:
        res = self.request("initialize", {
            "protocolVersion": _PROTOCOL_VERSION,
            "capabilities": {"roots": {"listChanged": False}},
            "clientInfo": {"name": "bcaldata-mcp", "version": "1"},
        }, timeout=min(self.timeout, 90))
        self.server_info = res.get("serverInfo", {})
        self._notify("notifications/initialized")
        try:
            self.tools = self.list_tools()
        except MCPError:
            self.tools = []

    def list_tools(self) -> list[dict]:
        return self.request("tools/list").get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None, *,
                  timeout: float | None = None) -> dict:
        res = self.request("tools/call", {"name": name, "arguments": arguments or {}},
                           timeout=timeout)
        if res.get("isError"):
            raise MCPError(f"{self.name}: tool {name} returned error: {_text(res)}")
        return res

    def call_tool_text(self, name: str, arguments: dict | None = None, **kw: object) -> str:
        return _text(self.call_tool(name, arguments, **kw))

    def call_tool_json(self, name: str, arguments: dict | None = None, **kw: object) -> object:
        txt = self.call_tool_text(name, arguments, **kw)
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return txt


def _text(result: dict) -> str:
    """Join the text blocks of an MCP tool result / structured content."""
    if not isinstance(result, dict):
        return str(result)
    if "structuredContent" in result and result["structuredContent"] is not None:
        sc = result["structuredContent"]
        return sc if isinstance(sc, str) else json.dumps(sc)
    parts = []
    for block in result.get("content", []) or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)


# --------------------------------------------------------------------------
# AL MCP server


class ALMcp:
    """`al launchmcpserver --transport stdio` — compile / build / diagnostics / tests."""

    def __init__(self, *, package_cache: str | Path | None = None,
                 analyzers: bool = True, timeout: float = 180.0,
                 projects: list[str | Path] | None = None) -> None:
        args = [AL_BIN, "launchmcpserver", "--transport", "stdio", "--nolog", "--noauth"]
        for p in projects or []:
            args.append(str(Path(p).resolve()))
        if package_cache is None:
            from .verify import _shared_alpackages

            package_cache = _shared_alpackages()
        args += ["--packagecachepath", str(package_cache)]
        if analyzers:
            from .alsp import _analyzer_dlls, _artifact_platform_dir

            dlls = _analyzer_dlls()
            if dlls:
                args += ["--codeanalyzers", ",".join(dlls)]
            plat = _artifact_platform_dir()
            if plat:
                args += ["--assemblyprobingpaths", plat]
        self.mcp = MCPClient(args, timeout=timeout, name="al-mcp")

    def start(self) -> "ALMcp":
        self.mcp.start()
        return self

    def __enter__(self) -> "ALMcp":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.mcp.close()

    def close(self) -> None:
        self.mcp.close()

    def tool_names(self) -> list[str]:
        return [t.get("name", "") for t in self.mcp.tools]

    def add_project(self, project_dir: str | Path) -> str:
        return self.mcp.call_tool_text("al_addproject", {"projectPath": str(Path(project_dir).resolve())})

    def compile(self, project_dir: str | Path, *, enable_code_analysis: bool = False,
                only_errors: bool = False, max_diagnostics: int | None = None,
                timeout: float | None = None) -> object:
        opts: dict = {"onlyErrors": only_errors, "enableCodeAnalysis": enable_code_analysis}
        if max_diagnostics is not None:
            opts["maxDiagnosticsPerCompilation"] = max_diagnostics
        return self.mcp.call_tool_json(
            "al_compile",
            {"projectPath": str(Path(project_dir).resolve()), "options": opts},
            timeout=timeout)

    def build(self, project_dir: str | Path) -> object:
        return self.mcp.call_tool_json("al_build", {"projectPath": str(Path(project_dir).resolve())})

    def get_diagnostics(self, *, file_path: str | Path | None = None,
                        folder_path: str | Path | None = None,
                        project_path: str | Path | None = None,
                        severities: list[str] | None = None,
                        areas: list[str] | None = None) -> object:
        args: dict = {}
        if file_path:
            args["filePath"] = str(Path(file_path).resolve())
        if folder_path:
            args["folderPath"] = str(Path(folder_path).resolve())
        if project_path:
            args["projectPath"] = str(Path(project_path).resolve())
        if severities:
            args["severities"] = severities
        if areas:
            args["areas"] = areas
        return self.mcp.call_tool_json("al_getdiagnostics", args)

    def run_tests(self, project_dir: str | Path, **kw: object) -> object:
        return self.mcp.call_tool_json("al_run_tests",
                                       {"projectPath": str(Path(project_dir).resolve()), **kw})


# --------------------------------------------------------------------------
# ALCops MCP server


def alcops_mcp_command() -> list[str] | None:
    """The `alcops-mcp` global tool if installed, else a `dotnet run` on the vendored source."""
    exe = shutil.which("alcops-mcp")
    if exe:
        return [exe]
    built = list((Path.home() / "bc-al-data" / "vendor" / "mcp-server").glob(
        "src/ALCops.Mcp/bin/*/net*/ALCops.Mcp.dll"))
    if built:
        return [str(Path(_DOTNET_ROOT) / "dotnet"), str(built[0])]
    return None


class ALCopsMcp:
    """ALCops MCP: `analyze`, `list_rules`, `get_fixes`, `apply_fix`, `apply_fix_all`.

    `apply_fix` writes the fixed content to disk and returns the new file text,
    which G8 pairs against the pre-fix text.
    """

    def __init__(self, *, timeout: float = 180.0,
                 command: list[str] | None = None) -> None:
        cmd = command or alcops_mcp_command()
        if cmd is None:
            raise MCPError(
                "alcops-mcp not available: not on PATH and vendor/mcp-server is not built. "
                "See PIPELINE.md 'Known gaps'.")
        env = {}
        alcops = os.environ.get("ALCOPS_DIR")
        if alcops:
            env["BCDEVELOPMENTTOOLSPATH"] = str(Path(alcops).parent)
        self.mcp = MCPClient(cmd, env=env, timeout=timeout, name="alcops-mcp")

    def start(self) -> "ALCopsMcp":
        self.mcp.start()
        return self

    def __enter__(self) -> "ALCopsMcp":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.mcp.close()

    def close(self) -> None:
        self.mcp.close()

    def list_rules(self) -> list[dict]:
        res = self.mcp.call_tool_json("list_rules", {})
        if isinstance(res, dict):
            return res.get("rules", res.get("items", []))
        return res if isinstance(res, list) else []

    def analyze(self, *, project: str | Path | None = None,
                file: str | Path | None = None,
                cop_filter: str | None = None) -> object:
        """Real schema: projectPath (required), filePath (optional), copFilter (csv, optional)."""
        args: dict = {}
        if project:
            args["projectPath"] = str(Path(project).resolve())
        if file:
            args["filePath"] = str(Path(file).resolve())
        if cop_filter:
            args["copFilter"] = cop_filter
        return self.mcp.call_tool_json("analyze", args)

    @staticmethod
    def _fix_args(project: str | Path, diagnostic: dict) -> dict:
        """apply_fix / get_fixes want projectPath + filePath + diagnosticId + line (1-based)."""
        return {
            "projectPath": str(Path(project).resolve()),
            "filePath": str(Path(diagnostic["filePath"]).resolve()),
            "diagnosticId": diagnostic.get("id") or diagnostic.get("diagnosticId"),
            "line": diagnostic.get("startLine") or diagnostic.get("line"),
        }

    def get_fixes(self, project: str | Path, diagnostic: dict) -> object:
        return self.mcp.call_tool_json("get_fixes", self._fix_args(project, diagnostic))

    def apply_fix(self, project: str | Path, diagnostic: dict, *,
                  equivalence_key: str | None = None) -> str:
        """Apply a code fix for `diagnostic`; return the file text after the write."""
        args = self._fix_args(project, diagnostic)
        if equivalence_key:
            args["equivalenceKey"] = equivalence_key
        out = self.mcp.call_tool_text("apply_fix", args)
        try:
            return Path(diagnostic["filePath"]).read_text()
        except OSError:
            return out

    def apply_fix_all(self, *, project: str | Path | None = None,
                      file: str | Path | None = None, rule_id: str,
                      dry_run: bool = False) -> object:
        args: dict = {"diagnosticId": rule_id, "dryRun": dry_run,
                      "scope": "document" if file else "project"}
        if project:
            args["projectPath"] = str(Path(project).resolve())
        if file:
            args["filePath"] = str(Path(file).resolve())
        return self.mcp.call_tool_json("apply_fix_all", args)
