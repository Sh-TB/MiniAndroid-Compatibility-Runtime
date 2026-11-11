#!/usr/bin/env python3
"""S214 sweep: all comments after watermark 6778202729 across hot threads."""
import json, subprocess, sys, os

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
WATERMARK = 6787176796
ME = "Sh-TB"

def token():
    out = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project/miniandroid",
                         input="protocol=https\nhost=github.com\n", capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

TOK = token()

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

issues = api(f"https://api.github.com/repos/{REPO}/issues?state=all&sort=updated&direction=desc&per_page=60")
new_comments = []
new_issues = []
for iss in issues:
    n = iss["number"]
    if iss.get("pull_request"):
        continue
    # new issues created after watermark time need body check regardless of comments
    total = iss.get("comments", 0)
    got = 0
    page = 1
    while got < total + 100 and page < 6:
        batch = api(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={page}")
        if not batch:
            break
        got += len(batch)
        for c in batch:
            if c["id"] > WATERMARK:
                new_comments.append((n, c["id"], c["user"]["login"], c["created_at"],
                                     len(c.get("body") or "")))
        page += 1
    if n not in [x[0] for x in new_comments] and iss["created_at"] > "2026-11-10T20:20":
        new_issues.append((n, iss["created_at"], (iss.get("title") or "")[:80]))

new_comments.sort(key=lambda x: x[3])
print(f"=== {len(new_comments)} comments after watermark {WATERMARK} ===")
for n, cid, user, ts, blen in new_comments:
    print(f"#{n} c={cid} @{user} {ts} len={blen}")
print(f"=== possibly-new issues with 0 comments: {new_issues} ===")
