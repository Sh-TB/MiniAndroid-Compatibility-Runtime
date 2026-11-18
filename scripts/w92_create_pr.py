#!/usr/bin/env python3
"""W9.2: create the PR for wave9/dev-so-clean with the exact required title,
then verify it exists. Token read from git config, never printed."""
import json, subprocess, re, sys

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
TITLE = "ISSUE-612: Add opt-in shared Dalvik .so development build path"
body = open("/home/z/my-project/download/wave9_pr_body_clean.md").read()
data = {"title": TITLE, "head": "wave9/dev-so-clean", "base": "main", "body": body}
out = subprocess.run(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
                      "-H", "Content-Type: application/json", "-d", json.dumps(data), f"{BASE}/pulls"],
                     capture_output=True, text=True).stdout
d = json.loads(out)
if d.get("number"):
    n = d["number"]
    # verify existence via independent GET
    v = json.loads(subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {tok}", f"{BASE}/pulls/{n}"],
                                  capture_output=True, text=True).stdout)
    print(json.dumps({"created": True, "number": v.get("number"), "url": v.get("html_url"),
                      "state": v.get("state"), "title": v.get("title"),
                      "head_ref": (v.get("head") or {}).get("ref"),
                      "base_ref": (v.get("base") or {}).get("ref"),
                      "base_sha": (v.get("base") or {}).get("sha", "")[:12],
                      "head_sha": (v.get("head") or {}).get("sha", "")[:12],
                      "mergeable": v.get("mergeable"), "mergeable_state": v.get("mergeable_state"),
                      "draft": v.get("draft")}, indent=1))
else:
    print(json.dumps({"created": False, "reason": d.get("message", "unknown"),
                      "errors": d.get("errors", "")}, indent=1))
