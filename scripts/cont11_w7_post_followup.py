#!/usr/bin/env python3
"""CONT-11 WAVE 7 — post the rebased 'PROBLEM SOLVED' follow-up to Issue #380."""
import subprocess, json, urllib.request, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 380

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}

BODY = open("/home/z/my-project/tmp/cont11_w8_ledger.md", encoding="utf-8").read()

# Guard: refuse duplicate posting if an identical body tail is already present.
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments?per_page=10",
    headers=HDRS)
with urllib.request.urlopen(req) as r:
    existing = json.loads(r.read())
for c in existing:
    if "CONT-11 WAVE 8 — batch 2 of 20" in c.get("body", ""):
        print("ALREADY POSTED as comment id:", c["id"])
        sys.exit(0)

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode("utf-8"),
    headers={**HDRS, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as r:
    resp = json.loads(r.read())
print("posted comment id:", resp["id"])
