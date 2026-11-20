#!/usr/bin/env python3
"""S18-8 dedupe check: list recent #635 comments (GET only). Token in-process."""
import json, subprocess, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}/issues/635/comments?per_page=100"

creds = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project",
                       input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True)
token = ""
for line in creds.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    raise SystemExit("no stored credential — aborting (nothing printed)")
req = urllib.request.Request(API, headers={
    "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
    "User-Agent": "miniandroid-audit"})
with urllib.request.urlopen(req) as r:
    comments = json.load(r)
print(f"total comments on #635: {len(comments)}")
for c in comments[-6:]:
    first = c["body"].strip().splitlines()[0][:100]
    print(f"  {c['id']} {c['created_at']} :: {first}")
