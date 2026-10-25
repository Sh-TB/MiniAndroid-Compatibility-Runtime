#!/usr/bin/env python3
"""CONT-32 — read the LATEST comment on #387 + #364 recent directives."""
import subprocess, json, urllib.request

def token():
    out = subprocess.run(["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOK = token()

def api(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}",
        headers={"Authorization": f"token {TOK}", "User-Agent": "cont32-selfupdate"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

print("=== #387 LATEST COMMENT (absolute last) ===")
cs = api("issues/387/comments?per_page=2")
for c in cs[-1:]:
    print(f"comment {c['id']} at {c['created_at']}:")
    print(c["body"][:2500])

print("\n=== #364 LATEST 2 COMMENTS ===")
cs = api("issues/364/comments?per_page=2")
for c in cs:
    print(f"--- comment {c['id']} at {c['created_at']}:")
    print(c["body"][:1200])
    print()
