#!/usr/bin/env python3
"""S230: full re-pull of issues 582-587 (bodies + all comments) to rebuild the
authoritative checklist. Saves JSON under evidence/s230/. Prints per-issue
summary: issue title/state, body updated_at, comment count, last comment id/time."""
import json, subprocess, os
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/s230"
os.makedirs(OUT, exist_ok=True)

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s230-fetch"})
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

summary = {}
for num in (582, 583, 584, 585, 586, 587):
    issue = api(f"https://api.github.com/repos/{REPO}/issues/{num}")
    with open(f"{OUT}/issue{num}.json", "w") as f:
        json.dump(issue, f, indent=1)
    comments = paged(f"https://api.github.com/repos/{REPO}/issues/{num}/comments")
    with open(f"{OUT}/issue{num}_comments.json", "w") as f:
        json.dump(comments, f, indent=1)
    last = comments[-1] if comments else None
    summary[num] = {
        "title": issue["title"],
        "state": issue["state"],
        "created": issue["created_at"],
        "body_updated": issue["updated_at"],
        "user": issue["user"]["login"],
        "n_comments": len(comments),
        "last_comment_id": last["id"] if last else None,
        "last_comment_at": last["created_at"] if last else None,
        "last_comment_user": last["user"]["login"] if last else None,
    }
    print(num, json.dumps(summary[num], ensure_ascii=False))

with open(f"{OUT}/summary.json", "w") as f:
    json.dump(summary, f, indent=1)
print("\nsaved to", OUT)
