#!/usr/bin/env python3
"""S15-d: post the #635 progress comment and the #626 classification comment.
Token comes from `git credential fill` — used only in-process, never printed."""
import json, subprocess, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TARGETS = [
    ("/home/z/my-project/scripts/s15_635_comment_body.md", f"https://api.github.com/repos/{REPO}/issues/635/comments"),
    ("/home/z/my-project/scripts/s15_626_comment_body.md", f"https://api.github.com/repos/{REPO}/issues/626/comments"),
]

creds = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project",
                       input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True)
token = ""
for line in creds.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    raise SystemExit("no stored credential — aborting (nothing printed)")

for body_path, api in TARGETS:
    payload = json.dumps({"body": open(body_path, encoding="utf-8").read()}).encode()
    req = urllib.request.Request(api, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "Content-Type": "application/json", "User-Agent": "miniandroid-audit"})
    try:
        with urllib.request.urlopen(req) as r:
            print("POSTED:", json.load(r).get("html_url", "(no url)"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read()[:300].decode(errors="ignore"))
        sys.exit(1)
