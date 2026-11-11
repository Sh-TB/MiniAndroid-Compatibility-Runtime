#!/usr/bin/env python3
"""Deep edit scan: over ALL repo comments (1778), list every comment whose
updated_at is meaningfully later than created_at (ever edited), sorted by
updated_at desc, focusing on the recent window. Also detect issue-body edits:
issue.updated_at > last_comment_time + margin."""
import json, subprocess, sys, urllib.request
from datetime import datetime, timedelta

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
cred = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=",1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json", "User-Agent": "s215-edit-scan"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def paged(url):
    out, page = [], 1
    while True:
        sep = "&" if "?" in url else "?"
        b = api(f"{url}{sep}per_page=100&page={page}")
        if not b: break
        out.extend(b)
        if len(b) < 100: break
        page += 1
    return out

comments = paged(f"https://api.github.com/repos/{REPO}/issues/comments?per_page=100&sort=created&direction=asc")
print(f"total comments: {len(comments)}")

def ts(s): return datetime.fromisoformat(s.replace("Z","+00:00"))

# S214 session started ~04:20Z today; sweep cutoff conservative 04:00Z
CUTOFF = ts("2026-11-11T04:00:00Z")
edited_recent = [c for c in comments if ts(c["updated_at"]) > CUTOFF]
print(f"\n=== comments touched (created OR updated) after {CUTOFF.isoformat()} ({len(edited_recent)}) ===")
for c in sorted(edited_recent, key=lambda x: x["updated_at"]):
    d = (ts(c["updated_at"]) - ts(c["created_at"])).total_seconds()
    tag = "EDITED" if d > 120 else "new   "
    issue = c["issue_url"].rsplit("/",1)[-1]
    body = (c.get("body") or "").replace("\n"," ")
    print(f"[{tag}] c={c['id']} #{issue} cr={c['created_at']} up={c['updated_at']} "
          f"delta={d/60:.0f}m :: {body[:120]}")

# ever-edited with delta > 10 min, updated in last 36h
C36 = ts("2026-11-09T17:00:00Z")
ever = [c for c in comments
        if ts(c["updated_at"]) > C36 and (ts(c["updated_at"])-ts(c["created_at"])).total_seconds() > 600]
print(f"\n=== ever-edited (>10min delta) updated after {C36.isoformat()} ({len(ever)}) ===")
for c in sorted(ever, key=lambda x: x["updated_at"]):
    d = (ts(c["updated_at"]) - ts(c["created_at"])).total_seconds()
    issue = c["issue_url"].rsplit("/",1)[-1]
    body = (c.get("body") or "").replace("\n"," ")
    print(f"c={c['id']} #{issue} cr={c['created_at']} up={c['updated_at']} "
          f"delta={d/3600:.1f}h :: {body[:120]}")

# issue body edit detection: issue updated_at > last comment created_at + 60s
issues = paged(f"https://api.github.com/repos/{REPO}/issues?state=all&sort=updated&direction=desc&per_page=60")
print(f"\n=== issue-body-edit suspects (top 60 recent) ===")
for i in issues:
    if "pull_request" in i: continue
    up, cr = ts(i["updated_at"]), ts(i["created_at"])
    if up <= CUTOFF: continue
    cs = paged(f"https://api.github.com/repos/{REPO}/issues/{i['number']}/comments") if False else None
    # cheaper: fetch only last comment
    lc = api(f"https://api.github.com/repos/{REPO}/issues/{i['number']}/comments?per_page=1&sort=created&direction=desc")
    last_c = ts(lc[0]["created_at"]) if lc else cr
    if up > last_c + timedelta(seconds=60):
        print(f"#{i['number']} up={i['updated_at']} last_comment={last_c.isoformat()} "
              f"BODY-EDITED :: {i['title'][:80]}")
print("\ndone")
