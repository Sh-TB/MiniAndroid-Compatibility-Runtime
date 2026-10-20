#!/usr/bin/env python3
"""Fetch issue #364 body + ALL comments (paginated) for the current wave."""
import subprocess, json, urllib.request, os, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "forensic"}

os.makedirs("/home/z/my-project/tmp", exist_ok=True)

def api(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}", headers=HDRS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

issue = api("issues/364")
print(f"ISSUE 364: state={issue['state']} comments={issue['comments']}")
print(f"TITLE: {issue['title']}")
body = issue['body'] or ''
open("/home/z/my-project/tmp/i364_body.txt", "w").write(body)
print(f"BODY saved ({len(body)} chars), first 3 lines:")
print("\n".join(body.strip().split("\n")[:3]))

all_comments, page = [], 1
while True:
    cs = api(f"issues/364/comments?per_page=100&page={page}")
    if not cs:
        break
    all_comments.extend(cs)
    page += 1
    if page > 30:
        break

json.dump(all_comments, open("/home/z/my-project/tmp/i364_comments_all.json", "w"), indent=1)
print(f"\nTOTAL comments fetched: {len(all_comments)}")
print("--- last 25 comment headers ---")
for c in all_comments[-25:]:
    body = c['body'] or ''
    first = body.strip().split("\n")[0][:120]
    print(c['id'], c['created_at'], repr(first))
