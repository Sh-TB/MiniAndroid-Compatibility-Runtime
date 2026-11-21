#!/usr/bin/env python3
"""S16-d: post the S16 progress comment on #635. Token from git credential fill, in-process only."""
import json, subprocess, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}/issues/635/comments"

creds = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project",
                       input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True)
token = ""
for line in creds.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    raise SystemExit("no stored credential — aborting (nothing printed)")

payload = json.dumps({"body": open("/home/z/my-project/scripts/s18_cont2_comment_body.md", encoding="utf-8").read()}).encode()
req = urllib.request.Request(API, data=payload, method="POST", headers={
    "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
    "Content-Type": "application/json", "User-Agent": "miniandroid-audit"})
try:
    with urllib.request.urlopen(req) as r:
        print("POSTED:", json.load(r).get("html_url", "(no url)"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:300].decode(errors="ignore"))
    sys.exit(1)
