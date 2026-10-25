#!/usr/bin/env python3
"""CONT-32 — read current GitHub issue state for self-update (latest comments on #387 + open issues list)."""
import subprocess, json, urllib.request

def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOK = token()

def api(path):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        headers={"Authorization": f"token {TOK}", "User-Agent": "cont32-selfupdate"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

issues = api("issues?state=all&per_page=15&sort=updated")
print("=== RECENTLY UPDATED ISSUES ===")
for i in issues:
    print(f"#{i['number']} [{i['state']}] {i['title'][:100]} (updated {i['updated_at']}, comments {i['comments']})")

print("\n=== #387 LAST COMMENTS ===")
for c in api("issues/387/comments?per_page=4")[-4:]:
    body = c["body"][:1500]
    print(f"--- comment {c['id']} at {c['created_at']}:")
    print(body)
    print()
