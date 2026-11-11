#!/usr/bin/env python3
"""Robust body-edit detection: fetch ALL comments once, group by issue,
compute max(created_at, updated_at) per issue, compare vs issue.updated_at.
Any issue whose updated_at > last comment activity => body/title/state edited.
Print the flagged issues with title + a body preview, and save bodies of the
3 new S215 comments (#581 part1/part2, #577 cross-link, #536 registration)."""
import json, subprocess, urllib.request
from datetime import datetime

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
cred = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=",1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json", "User-Agent": "s215-body-scan"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def paged(url):
    out, page = [], 1
    while True:
        b = api(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}")
        if not b: break
        out.extend(b)
        if len(b) < 100: break
        page += 1
    return out

def ts(s): return datetime.fromisoformat(s.replace("Z","+00:00"))

comments = paged(f"https://api.github.com/repos/{REPO}/issues/comments")
print(f"comments: {len(comments)}")
last_act = {}  # issue_number -> latest datetime of any comment activity
for c in comments:
    n = int(c["issue_url"].rsplit("/",1)[-1])
    t = max(ts(c["created_at"]), ts(c["updated_at"]))
    if n not in last_act or t > last_act[n]:
        last_act[n] = t

issues = paged(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&sort=updated")
print(f"issues fetched: {len(issues)}")
CUTOFF = ts("2026-11-09T00:00:00Z")
flagged = []
for i in issues:
    if "pull_request" in i: continue
    up = ts(i["updated_at"])
    if up < CUTOFF: continue
    la = last_act.get(i["number"], ts(i["created_at"]))
    if up > la:
        flagged.append((i, up, la))

print(f"\n=== BODY-EDITED issues since 11-09 ({len(flagged)}) ===")
for i, up, la in sorted(flagged, key=lambda x: x[1]):
    body = (i.get("body") or "").replace("\n"," ")
    print(f"#{i['number']} up={up.isoformat()} last_comment={la.isoformat()} :: {i['title'][:70]}")
    print(f"    body[:180]: {body[:180]}")
