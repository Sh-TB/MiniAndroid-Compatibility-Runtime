#!/usr/bin/env python3
"""S220: check W21 17/17 part arrival on issue #575."""
import json, subprocess

TOKEN = None
r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                   capture_output=True, text=True, cwd="/home/z/my-project")
for line in r.stdout.splitlines():
    if line.startswith("password="):
        TOKEN = line.split("=", 1)[1]

API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/575/comments"
comments = []
page = 1
while True:
    cmd = ["curl", "-sS", "-H", f"Authorization: token {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           f"{API}?per_page=100&page={page}"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    batch = json.loads(out.stdout)
    if not batch:
        break
    comments.extend(batch)
    if len(batch) < 100:
        break
    page += 1

print(f"total comments on #575: {len(comments)}")
# scan for part markers
for c in comments:
    body = c['body']
    for m in ['PART 17', 'part 17', '17/17', 'Part 17']:
        if m in body:
            print(f"--- id={c['id']} {c['created_at']} contains '{m}':")
            idx = body.find(m)
            print(body[max(0,idx-200):idx+400].replace('\n', ' | ')[:600])
            break
# also print last 3 comments' headers
for c in comments[-3:]:
    print("=" * 60)
    print(f"id={c['id']} at={c['created_at']} len={len(c['body'])}")
    print(c['body'][:500].replace('\n', ' | '))
