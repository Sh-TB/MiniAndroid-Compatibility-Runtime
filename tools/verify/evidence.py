#!/usr/bin/env python3
"""Evidence Bundle collector (brief §7/§8, speed-addendum §58).
Wraps ONE command execution into evidence/<run-id>/ with full provenance.
Statuses never mixed: RESEARCHED..UNPROVEN vocabulary (brief §8)."""
import hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/tools/verify
REPO = os.path.dirname(os.path.dirname(HERE))       # repo root
EVID = os.path.join(REPO, "evidence")

def git(*a):
    return subprocess.run(["git", "-C", REPO,
                           *a], capture_output=True, text=True).stdout.strip()

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def collect(cmd, run_id, apk=None, status="OBSERVED", env_gate=None, cwd=None):
    t0 = time.time()
    rid = f"{time.strftime('%Y%m%d-%H%M%S')}-{run_id}"
    out = os.path.join(EVID, rid)
    os.makedirs(out, exist_ok=True)
    e = dict(os.environ)
    if env_gate:
        e.update(env_gate)
    r = subprocess.run(cmd, capture_output=True, text=True, env=e,
                       cwd=cwd or os.path.join(REPO, "miniandroid"))
    open(os.path.join(out, "command.txt"), "w").write(" ".join(cmd))
    open(os.path.join(out, "stdout.log"), "w").write(r.stdout[-4_000_000:])
    open(os.path.join(out, "stderr.log"), "w").write(r.stderr[-4_000_000:])
    hashes = {}
    for k, p in (("apk", apk),):
        if p and os.path.exists(p):
            hashes[k + "_sha256"] = sha256_file(p)
    manifest = {
        "run_id": rid, "commit": git("rev-parse", "HEAD"),
        "apk_sha256": hashes.get("apk_sha256"),
        "status": status if r.returncode == 0 else "FAILED",
        "exit_code": r.returncode, "started_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)),
        "duration_ms": int((time.time() - t0) * 1000),
        "command": " ".join(cmd), "tool": "evidence.py/1.0",
        "env_gates": env_gate or {},
    }
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    json.dump(hashes, open(os.path.join(out, "hashes.json"), "w"), indent=1)
    json.dump({"stdout_bytes": len(r.stdout), "stderr_bytes": len(r.stderr)},
              open(os.path.join(out, "metrics.json"), "w"), indent=1)
    return out, manifest

if __name__ == "__main__":
    # usage: evidence.py <run-id> [--apk path] -- <cmd...>
    args = sys.argv[1:]
    run_id = args[0]
    apk = None
    if "--apk" in args:
        i = args.index("--apk"); apk = args[i + 1]; del args[i:i + 2]
    cmd = args[args.index("--") + 1:]
    out, m = collect(cmd, run_id, apk)
    print(json.dumps(m, indent=1))
    print("bundle:", out)
