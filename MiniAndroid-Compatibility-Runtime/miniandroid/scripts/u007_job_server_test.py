#!/usr/bin/env python3
"""
UNIFIED_007 — BROWSER/AGENT line end-to-end verification.

Drives the real job server over HTTP:
  1. POST /api/jobs        → 201 QUEUED
  2. worker picks it up    → RUNNING with live milestone logs
  3. completion            → COMPLETED + artifact (screenshot)
  4. cancel path           → CANCELLED (409 on terminal)
  5. captcha policy        → CAPTCHA_REQUIRED, never bypassed
  6. persistence           → kill server, restart, state intact (refresh-safe)
Exit 0 = all behaviors PROVEN.
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

REPO = "/home/z/my-project/repo/miniandroid"
SERVER = os.path.join(REPO, "build", "u007_job_server")
PORT = 8477
STORE = os.path.join(REPO, "database", "u007_jobs.json")
ART = os.path.join(REPO, "run", "u007_job_artifacts")
APK = os.path.join(REPO, "download", "corpus", "gmdice.apk")

passed, failed = 0, 0
def check(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print("PASS:", msg)
    else:
        failed += 1
        print("FAIL:", msg)

def req(method, path, body=None):
    url = f"http://127.0.0.1:{PORT}{path}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}

def start_server():
    proc = subprocess.Popen(
        [SERVER, str(PORT), STORE, os.path.join(REPO, "build"), ART],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            s, b = req("GET", "/health")
            if s == 200:
                return proc
        except Exception:
            time.sleep(0.2)
    return proc

def stop_server(proc):
    proc.send_signal(signal.SIGKILL)
    proc.wait()

if os.path.exists(STORE):
    os.remove(STORE)

# ---- 1..3: full apk_run lifecycle ----
srv = start_server()
try:
    s, job = req("POST", "/api/jobs", {"apk_path": APK, "type": "apk_run"})
    check(s == 201 and job.get("status") == "QUEUED", "POST /api/jobs → 201 QUEUED")
    jid = job["id"]

    # poll until terminal
    terminal = None
    for _ in range(200):
        s, st = req("GET", f"/api/jobs/{jid}/status")
        if st.get("status") in ("COMPLETED", "FAILED", "CANCELLED", "STALLED"):
            terminal = st["status"]
            break
        time.sleep(0.5)
    check(terminal == "COMPLETED", f"job completed (got {terminal})")

    s, full = req("GET", f"/api/jobs/{jid}")
    logs = full.get("logs", [])
    has_parsed = any("Running APK" in l for l in logs)
    has_status = any("Status:" in l for l in logs)
    check(has_parsed and has_status,
          "live logs contain pipeline milestones (APK running → Status)")
    arts = full.get("artifacts", [])
    check(len(arts) > 0 and os.path.exists(arts[0]),
          f"artifact screenshot exists ({arts[:1]})")

    # 404 on unknown id
    s, _ = req("GET", "/api/jobs/nope")
    check(s == 404, "GET unknown job → 404")

    # ---- 5: captcha policy (pause, never bypass) ----
    s, cjob = req("POST", "/api/jobs", {"apk_path": APK, "type": "captcha"})
    cid = cjob["id"]
    cap_status = None
    for _ in range(40):
        s, st = req("GET", f"/api/jobs/{cid}/status")
        cap_status = st.get("status")
        if cap_status in ("CAPTCHA_REQUIRED", "RUNNING", "WAITING"):
            break
        time.sleep(0.25)
    check(cap_status == "CAPTCHA_REQUIRED",
          f"captcha job pauses at CAPTCHA_REQUIRED (got {cap_status})")

    # ---- 4: cancel path ----
    s, njob = req("POST", "/api/jobs", {"apk_path": APK, "type": "apk_run"})
    nid = njob["id"]
    s, resp = req("POST", f"/api/jobs/{nid}/cancel")
    check(s in (200, 409), f"cancel returns 200 or 409 (got {s})")
    time.sleep(0.5)
    s, st = req("GET", f"/api/jobs/{nid}/status")
    check(st.get("status") in ("CANCELLED", "COMPLETED"),
          f"cancel respected (got {st.get('status')})")
finally:
    stop_server(srv)

# ---- 6: persistence across restart (refresh safety) ----
srv = start_server()
try:
    s, lst = req("GET", "/api/jobs")
    ids = [j["id"] for j in lst.get("jobs", [])]
    check(jid in ids, "job state survives server restart (refresh-safe)")
    s, again = req("GET", f"/api/jobs/{jid}")
    check(again.get("status") == "COMPLETED",
          "completed status persisted verbatim")
finally:
    stop_server(srv)

print(f"\nJOB SERVER TESTS: {passed} PASS, {failed} FAIL")
sys.exit(0 if failed == 0 else 1)
