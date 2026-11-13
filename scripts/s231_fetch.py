#!/usr/bin/env python3
"""S231: full re-pull of issues 582-587 (bodies + all comments) with edit
detection vs created_at. Baseline: S230 receipts posted at 2025-xx (ids
6857486367/6857486822/6857487275). Reports new/edited comments since then.
Saves JSON under evidence/s231/.
"""
import json, os, subprocess
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # R11 repo-root discovery
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = os.path.join(BASE, "evidence", "s231")
os.makedirs(OUT, exist_ok=True)

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=BASE).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s231-fetch"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def paged(url):
    out, page = [], 1
    while True:
        sep = "&" if "?" in url else "?"
        b = api(f"{url}{sep}per_page=100&page={page}")
        if not b:
            break
        out.extend(b)
        if len(b) < 100:
            break
        page += 1
    return out

S230_RECEIPTS = {6857486367, 6857486822, 6857487275}

for num in (582, 583, 584, 585, 586, 587):
    issue = api(f"https://api.github.com/repos/{REPO}/issues/{num}")
    with open(f"{OUT}/issue{num}.json", "w") as f:
        json.dump(issue, f, indent=1)
    comments = paged(f"https://api.github.com/repos/{REPO}/issues/{num}/comments")
    with open(f"{OUT}/issue{num}_comments.json", "w") as f:
        json.dump(comments, f, indent=1)
    print(f"=== #{num} [{issue['state']}] {issue['title']}")
    print(f"    body updated_at: {issue['updated_at']}  comments: {len(comments)}")
    for c in comments:
        edited = c["created_at"] != c["updated_at"]
        marker = ""
        if c["id"] in S230_RECEIPTS:
            marker = " [S230-RECEIPT]"
        elif c["created_at"] > "2025-12-25T00:00:00Z":
            marker = " [AFTER-S230]"
        ed = " EDITED" if edited else ""
        print(f"    {c['id']} {c['created_at']} by {c['user']['login']}{ed}{marker} len={len(c['body'])}")
    print()
