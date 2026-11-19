#!/usr/bin/env python3
"""W19-8 — post the P0 finalization evidence to Issue #612 (the P0 thread)."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 612

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}

BODY = open("evidence/p0_split/W19_FINAL_EVIDENCE.md",
            encoding="utf-8").read()

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode("utf-8"),
    headers={**HDRS, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as r:
    resp = json.loads(r.read())
print("posted comment id:", resp["id"], "to issue", ISSUE)
