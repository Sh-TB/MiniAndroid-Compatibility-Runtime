#!/usr/bin/env python3
"""S236.1 deep harness v2 (#596 §1.1): every run persists stdout, stderr,
exit code, command, duration, env overrides and timeout state as a JSON
sidecar beside the RAW .stdout/.stderr files. A run with no captured output
is a HARNESS FAIL, never a zero-marker success. Marker counts are derived
from the retained raw stdout only.

Self-tests (self_test()): a fake runner proves stdout-only, stderr-only,
mixed, non-zero-exit and missing-output behavior.
"""
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path

BIN = Path("/tmp/s236_audit/miniandroid/build/miniandroid")
UPLOAD = Path("/home/z/my-project/upload")
OUT = Path("/tmp/s236_audit/evidence/s236/deep_v2")
OUT.mkdir(parents=True, exist_ok=True)
CH = UPLOAD / "chess_jwtc_298.apk"
SU = UPLOAD / "opensudoku_v4113.apk"

class HarnessFail(Exception):
    pass

def run(cmd, tag, env=None, timeout=900):
    """Persist everything about one run; return the record."""
    rec = {"tag": tag,
           "cmd": [str(c) for c in cmd],
           "env": {k: v for k, v in (env or {}).items()},
           "timeout_s": timeout, "timed_out": False,
           "duration_s": None, "rc": None,
           "stdout_bytes": 0, "stderr_bytes": 0}
    t0 = time.time()
    try:
        r = subprocess.run(rec["cmd"], capture_output=True, text=True,
                           timeout=timeout,
                           env={**os.environ, **(env or {})})
        rec.update(rc=r.returncode, stdout=r.stdout, stderr=r.stderr,
                   duration_s=round(time.time() - t0, 2))
    except subprocess.TimeoutExpired as e:
        rec.update(timed_out=True,
                   stdout=(e.stdout or b"").decode(errors="replace"),
                   stderr=(e.stderr or b"").decode(errors="replace"),
                   duration_s=round(time.time() - t0, 2))
    rec["stdout_bytes"] = len(rec.get("stdout", ""))
    rec["stderr_bytes"] = len(rec.get("stderr", ""))
    raw_s = OUT / f"{tag}.stdout.log"
    raw_e = OUT / f"{tag}.stderr.log"
    raw_s.write_text(rec.get("stdout", ""))
    raw_e.write_text(rec.get("stderr", ""))
    if rec["stdout_bytes"] == 0 and rec["stderr_bytes"] == 0:
        raise HarnessFail(
            f"[{tag}] NO captured output on stdout OR stderr — refusing to "
            f"interpret as a zero-marker success (cmd: {rec['cmd'][:3]}...)")
    (OUT / f"{tag}.run.json").write_text(
        json.dumps({k: v for k, v in rec.items() if k not in
                    ("stdout", "stderr")}, indent=1) + "\n")
    return rec

def markers_from_raw(rec):
    """Parse ONLY the retained raw stdout file; assert it is non-empty."""
    raw = OUT / f"{rec['tag']}.stdout.log"
    if not raw.exists() or raw.stat().st_size == 0:
        raise HarnessFail(f"[{rec['tag']}] raw stdout missing/empty")
    txt = raw.read_text(errors="replace")
    return {m: txt.count(m) for m in (
        "C013-ONDRAW", "_fieldColor", "SQLITE-INSERT",
        "SQLITE-SHADOW] rawQuery rows=1", "CV-PUT", "F-NEW-65",
        "loadPGN", "FEN", "practice", "S191", "C102-ADAPTER",
        "getView", "TRY-ENTRY] Ljwtc/android/chess/helpers/MyPGNProvider",
        "Thread", "start()")}

def install(apk, store):
    r = run([BIN, "install", apk, "--data-root", store],
            tag=f"install_{Path(store).name}")
    apps = Path(store) / "data" / "app"
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith(".")
          and not d.name.endswith(".staging")
          and (d / "base.apk").exists()]
    return ds[0] if ds else None

def run_app(store, pkg, out, tag, frames, taps=None, env=None):
    cmd = [BIN, "run", "--execution-mode", "real-dalvik",
           "--data-root", store, "-o", out, "--package", pkg,
           "--frames", str(frames), "--frame-delay", "250"]
    for t in (taps or []):
        cmd += ["--tap", t]
    rec = run(cmd, tag=tag, env=env)
    rec["markers"] = markers_from_raw(rec)
    return rec

def census(store):
    rows = []
    for db in list(Path(store).rglob("*.db")) + list(Path(store).rglob("*.sqlite3")):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            for (t,) in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"):
                try:
                    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    if n:
                        rows.append({"db": db.name, "table": t, "rows": n})
                except sqlite3.Error:
                    pass
            con.close()
        except sqlite3.Error:
            pass
    return rows

def self_test():
    """§1.1 self-tests on a fake runner."""
    tmp = Path(tempfile.mkdtemp(prefix="s236_harness_selftest_"))
    fake = tmp / "fake_runner.sh"
    fake.write_text(
        '#!/bin/bash\n'
        'case "$1" in\n'
        '  stdout_only) echo "C013-ONDRAW x7" ;;\n'
        '  stderr_only) echo "err text" >&2 ;;\n'
        '  mixed) echo "C013-ONDRAW x3"; echo "E1" >&2 ;;\n'
        '  fail_nonzero) echo "partial C013-ONDRAW"; exit 3 ;;\n'
        '  silent) exit 0 ;;\n'
        'esac\n')
    fake.chmod(0o755)
    results = {}
    # stdout-only: rc 0, markers parsed from the retained raw stdout
    r = run([fake, "stdout_only"], tag="self_stdout")
    results["stdout_only"] = (r["rc"] == 0 and r["stdout_bytes"] > 0
                              and markers_from_raw(r)["C013-ONDRAW"] == 1)
    # stderr-only: passes the no-output guard via stderr
    r = run([fake, "stderr_only"], tag="self_stderr")
    results["stderr_only"] = (r["stderr_bytes"] > 0 and r["stdout_bytes"] == 0)
    # mixed: both retained, stdout parsed
    r = run([fake, "mixed"], tag="self_mixed")
    results["mixed"] = (r["stdout_bytes"] > 0 and r["stderr_bytes"] > 0
                        and markers_from_raw(r)["C013-ONDRAW"] == 1)
    # non-zero exit: rc preserved, NOT hidden
    r = run([fake, "fail_nonzero"], tag="self_nonzero")
    results["nonzero_rc_preserved"] = (r["rc"] == 3 and r["stdout_bytes"] > 0)
    # missing output: harness FAIL, never zero-markers
    try:
        run([fake, "silent"], tag="self_silent")
        results["silent_raises"] = False
    except HarnessFail:
        results["silent_raises"] = True
    (tmp / "selftest_results.json").write_text(
        json.dumps(results, indent=1) + "\n")
    ok = all(results.values())
    print("HARNESS SELF-TESTS:", json.dumps(results))
    print("SELFTEST:", "ALL PASS" if ok else "FAIL")
    return ok

if __name__ == "__main__":
    self_test()
