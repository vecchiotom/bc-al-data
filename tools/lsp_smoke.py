"""Minimal AL-LSP smoke: initialize, open the smoke codeunit, request documentSymbol + diagnostics."""
import json, os, subprocess, pathlib, sys

AL = os.path.expanduser("~/.dotnet/tools/al")
SMOKE = pathlib.Path.home() / "bc-al-data/.cache/smoke/app"
FILE = SMOKE / "src/HelloWorld.Codeunit.al"
env = {**os.environ, "DOTNET_ROOT": os.path.expanduser("~/.dotnet")}
p = subprocess.Popen([AL, "launchlspserver", str(SMOKE), "--nolog",
                      "--packagecachepath", str(SMOKE / ".alpackages")],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, bufsize=0)

def send(o):
    b = json.dumps(o).encode()
    p.stdin.write(f"Content-Length: {len(b)}\r\n\r\n".encode() + b); p.stdin.flush()

def readmsg():
    # skip any non-header banner lines until a Content-Length header
    while True:
        line = p.stdout.readline()
        if not line: return None
        if line.lower().startswith(b"content-length:"):
            n = int(line.split(b":")[1]); p.stdout.readline()  # blank line
            return json.loads(p.stdout.read(n))

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":os.getpid(),"rootUri":SMOKE.as_uri(),"capabilities":{}}})
send({"jsonrpc":"2.0","method":"initialized","params":{}})
send({"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":FILE.as_uri(),"languageId":"al","version":1,"text":FILE.read_text()}}})
send({"jsonrpc":"2.0","id":2,"method":"textDocument/documentSymbol","params":{"textDocument":{"uri":FILE.as_uri()}}})

diag_seen = sym_seen = False
for _ in range(200):
    m = readmsg()
    if m is None: break
    if m.get("method") == "textDocument/publishDiagnostics":
        d = m["params"]["diagnostics"]; diag_seen = True
        print(f"diagnostics ({len(d)}):", [f'{x.get("code")}: {x["message"][:60]}' for x in d[:6]])
    if m.get("id") == 2:
        r = m.get("result") or []; sym_seen = True
        print(f"documentSymbol: {len(r)} top-level")
        def walk(s, d=2):
            print(" "*d + f"{s['name']} (kind {s['kind']})")
            for c in s.get("children", []): walk(c, d+2)
        for s in r: walk(s)
    if sym_seen and diag_seen: break
send({"jsonrpc":"2.0","id":9,"method":"shutdown"}); send({"jsonrpc":"2.0","method":"exit"})
print("LSP SMOKE:", "OK" if sym_seen else "FAILED (no documentSymbol)")
sys.exit(0 if sym_seen else 1)
