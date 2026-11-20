#!/usr/bin/env python3
"""S14-g: post the #635 closeout comment via the GitHub REST API.
The token comes from `git credential fill` (the repo's stored credential) and
is used ONLY inside this process — never printed, never written to disk."""
import json, subprocess, sys, urllib.request

BODY_PATH = "/home/z/my-project/scripts/s14_635_comment_body.md"
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/635/comments"

creds = subprocess.run(
    ["git", "credential", "fill"], cwd="/home/z/my-project",
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True)
token = ""
for line in creds.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    raise SystemExit("no stored credential — aborting (nothing printed)")

body = open(BODY_PATH, encoding="utf-8").read()
payload = json.dumps({"body": body}).encode()
req = urllib.request.Request(API, data=payload, method="POST", headers={
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
    "User-Agent": "miniandroid-audit",
})
try:
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
        print("POSTED:", out.get("html_url", "(no url)"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:300].decode(errors="ignore"))
    sys.exit(1)
