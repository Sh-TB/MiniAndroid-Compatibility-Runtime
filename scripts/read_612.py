#!/usr/bin/env python3
"""Read issue #612 (critical) + its timeline from the MiniAndroid repo."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project/miniandroid").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "layout-audit"}

req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/612",
    headers=H)
with urllib.request.urlopen(req, timeout=30) as r:
    j = json.loads(r.read().decode())
print("STATE:", j["state"], "| title:", j["title"])
print("BODY:")
print(j["body"][:6000])

# also list open issues to see what else is open
req2 = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues?state=open&per_page=30",
    headers=H)
with urllib.request.urlopen(req2, timeout=30) as r:
    items = json.loads(r.read().decode())
print("\n--- OPEN ISSUES ---")
for it in items:
    if "pull_request" not in it:
        print(f"#{it['number']} [{it['state']}] {it['title'][:100]}")
