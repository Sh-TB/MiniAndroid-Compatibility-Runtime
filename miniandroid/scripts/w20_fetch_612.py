#!/usr/bin/env python3
"""W20-P1: paginate ALL #612 comments, save the two target IDs + summary."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TARGETS = {7002388310, 7002484385}

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}

allc, page = [], 1
while page <= 10:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/612/comments"
        f"?per_page=100&page={page}", headers=HDRS)
    with urllib.request.urlopen(req) as r:
        batch = json.loads(r.read())
    if not batch:
        break
    allc += batch
    page += 1
print(f"total #612 comments: {len(allc)}")
found = [c for c in allc if c["id"] in TARGETS]
for c in found:
    fn = f"evidence/w20/coder_{c['id']}.md"
    with open(fn, "w") as fh:
        fh.write(c["body"])
    print(f"saved {fn}: {len(c['body'])} chars by {c['user']['login']}")
missing = TARGETS - {c["id"] for c in allc}
if missing:
    print("MISSING:", missing)
    # list the newest 5 for reference
    for c in allc[-5:]:
        print(f"  recent: {c['id']} {c['created_at']} {len(c['body'])}ch")
