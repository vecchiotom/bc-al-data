"""AL compile gate — port of BC-Bench's compile-proxy app build to the mining pipeline.

Seeds an app project's `.alpackages` from the cached BC artifact (all shipped
`*.app` symbols), pins the runtime, and compiles with the full analyzer set.
Used to (a) baseline a real BCApps app, (b) verify a G5/G6 candidate.

Reference: ~/BC-Bench/src/bcbench/evaluate/{compile_proxy,bugfix}.py,
           ~/BC-Bench/src/bcbench/operations/bc_operations.py
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, tempfile
from dataclasses import dataclass, field
from pathlib import Path

ARTIFACT_CACHE = Path.home() / ".bcartifacts.cache" / "sandbox"
AL_BIN = os.environ.get("AL_BIN", str(Path.home() / ".dotnet/tools/al"))
ALCOPS_DIR = Path(os.environ["ALCOPS_DIR"]) if "ALCOPS_DIR" in os.environ else None
AL_COMPILER_DIR = Path(os.environ["AL_COMPILER_DIR"]) if "AL_COMPILER_DIR" in os.environ else None
_PLATFORM_TO_RUNTIME_OFFSET = 11
_ERROR_AL = re.compile(r"^\s*error AL\d+.*$", re.M)
_DIAG = re.compile(r"^.*?:\s*(error|warning|info)\s+([A-Z]{2}\d{3,4}i?):\s*(.*)$", re.M)


def artifact_root(version_major_minor: str) -> Path | None:
    roots = sorted(ARTIFACT_CACHE.glob(f"{version_major_minor}.*"))
    return roots[-1] if roots else None


def _app_json(app_dir: Path) -> dict:
    return json.loads((app_dir / "app.json").read_text(encoding="utf-8-sig"))


def symbol_version(app_dir: Path, fallback: str) -> str:
    """app.json `application` (or `platform`) major.minor if that artifact is cached, else fallback."""
    m = _app_json(app_dir)
    for key in ("application", "platform"):
        v = re.match(r"^(\d+\.\d+)", str(m.get(key) or ""))
        if v and artifact_root(v.group(1)) is not None:
            return v.group(1)
    return fallback


def seed_alpackages(app_dir: Path, version: str, *, build_from_source: list[str] | None = None) -> int:
    """Copy every *.app symbol from the artifact into app_dir/.alpackages, minus the
    names in `build_from_source` (default: this app's own name) so those compile from source."""
    root = artifact_root(version)
    if root is None:
        raise FileNotFoundError(f"no BC artifact {version}.* under {ARTIFACT_CACHE}")
    alp = app_dir / ".alpackages"
    if alp.is_dir():
        for f in alp.glob("*.app"):
            f.unlink()
    alp.mkdir(parents=True, exist_ok=True)
    shadow = [n.lower() for n in (build_from_source or [_app_json(app_dir).get("name", "")]) if n]
    n = 0
    for app in root.rglob("*.app"):
        if any(s in app.name.lower() for s in shadow):
            continue
        shutil.copy2(app, alp / app.name)
        n += 1
    return n


def pin_runtime(app_dir: Path) -> None:
    m = _app_json(app_dir)
    if m.get("runtime"):
        return
    pv = re.match(r"^(\d+)", str(m.get("platform") or ""))
    if not pv:
        return
    rt = int(pv.group(1)) - _PLATFORM_TO_RUNTIME_OFFSET
    if rt >= 1:
        m["runtime"] = f"{rt}.0"
        (app_dir / "app.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")


def _probing_paths(version: str) -> list[str]:
    root = artifact_root(version)
    if root is None:
        return []
    plat = root / "platform"
    return [str(plat)] if plat.is_dir() else []


def _analyzer_args() -> list[str]:
    if ALCOPS_DIR is None or AL_COMPILER_DIR is None:
        return []
    args = []
    for d in ("Common", "LinterCop", "PlatformCop", "FormattingCop",
              "ApplicationCop", "DocumentationCop", "TestAutomationCop"):
        p = ALCOPS_DIR / f"ALCops.{d}.dll"
        if p.is_file():
            args.append(f"/analyzer:{p}")
    cc = AL_COMPILER_DIR / "Microsoft.Dynamics.Nav.CodeCop.dll"
    if cc.is_file():
        args.append(f"/analyzer:{cc}")
    return args


@dataclass
class CompileResult:
    clean: bool                       # no `error AL`, .app written
    returncode: int
    app_written: bool
    errors: list[str] = field(default_factory=list)      # raw `error AL####` lines
    diagnostics: list[tuple[str, str, str]] = field(default_factory=list)  # (severity, code, msg)
    analyzer_hits: list[tuple[str, str]] = field(default_factory=list)     # (severity, code) for AA/AC/DC/FC/LC/PC/TA/UI
    stdout: str = ""

    @property
    def codes(self) -> set[str]:
        return {c for _, c, _ in self.diagnostics}


def compile_app(app_dir: Path, version: str, *, analyzers: bool = True,
                probing: list[str] | None = None) -> CompileResult:
    alp = app_dir / ".alpackages"
    args = [AL_BIN, "compile", f"/project:{app_dir}", f"/packagecachepath:{alp}"]
    probing = probing if probing is not None else _probing_paths(version)
    if probing:
        args.append("/assemblyprobingpaths:" + ",".join(probing))
    if analyzers:
        args += _analyzer_args()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.app"
        args.append(f"/out:{out}")
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False,
                           env={**os.environ, "DOTNET_ROOT": os.environ.get("DOTNET_ROOT", str(Path.home() / ".dotnet"))})
        text = (p.stdout or "") + (p.stderr or "")
        written = out.is_file()
        if written:
            (app_dir / "_compile_out.app").write_bytes(out.read_bytes())
    errs = _ERROR_AL.findall(text)
    diags = [(m.group(1), m.group(2), m.group(3).strip()) for m in _DIAG.finditer(text)]
    hits = [(s, c) for s, c, _ in diags if c[:2] in ("AA", "AC", "DC", "FC", "LC", "PC", "TA", "UI")]
    return CompileResult(
        clean=(not errs and written), returncode=p.returncode, app_written=written,
        errors=errs, diagnostics=diags, analyzer_hits=hits, stdout=text,
    )


def prepare(app_dir: Path, fallback_version: str = "28.0") -> str:
    """Seed symbols + pin runtime; return the resolved symbol version."""
    v = symbol_version(app_dir, fallback_version)
    seed_alpackages(app_dir, v)
    pin_runtime(app_dir)
    return v
