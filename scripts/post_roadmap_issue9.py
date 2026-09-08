#!/usr/bin/env python3
"""post_roadmap_issue9.py — publish MASTER-ROADMAP v3 as GitHub Issue #9 (living document).
Reads the 3 roadmap parts, merges them, JSON-encodes, POSTs via the API.
Token comes from /home/z/.gh_token (env GH_TOKEN_FILE overrides)."""
import json, os, sys, urllib.request

TOKEN = open(os.environ.get("GH_TOKEN_FILE", "/home/z/.gh_token")).read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = f"https://api.github.com/repos/{REPO}"

def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "miniandroid-campaign",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

parts = []
for p in ("roadmap_p1.md", "roadmap_p2.md", "roadmap_p3.md"):
    with open(f"/home/z/my-project/scripts/{p}") as f:
        parts.append(f.read())
body = "\n".join(parts)
print(f"roadmap body chars: {len(body)}")

title = "MASTER-ROADMAP v3 — MiniAndroid Compatibility Runtime — 100% Base Execution Closure System (living document)"
labels = ["documentation", "campaign"]
payload = {"title": title, "body": body, "labels": labels}
try:
    issue = api("/issues", "POST", payload)
except urllib.error.HTTPError as e:
    print(f"create failed: {e.code} {e.read().decode()[:500]}")
    # retry without labels
    issue = api("/issues", "POST", {"title": title, "body": body})
print(f"ISSUE CREATED: #{issue['number']}")
print(f"URL: {issue['html_url']}")
