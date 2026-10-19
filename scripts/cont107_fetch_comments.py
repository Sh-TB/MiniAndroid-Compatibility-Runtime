#!/usr/bin/env python3
"""CONT-107: fetch all #364 comments, list everything after the last processed ledger comment."""
import json, subprocess, sys

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
all_c = []
for p in range(1, 12):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}",
                        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/364/comments?per_page=100&page={p}"],
                       capture_output=True, text=True)
    try:
        cs = json.loads(r.stdout)
    except Exception as e:
        print(f"page {p} parse error: {e}"); break
    if not isinstance(cs, list) or not cs:
        break
    all_c += cs
    if len(cs) < 100:
        break

all_c.sort(key=lambda c: c["created_at"])
print("TOTAL COMMENTS:", len(all_c))
print("=== LAST 30 ===")
for c in all_c[-30:]:
    body = (c["body"] or "").strip().split("\n")[0][:120]
    print(c["id"], c["created_at"], c["user"]["login"], "|", body)
with open("/tmp/c364_all_sorted.json", "w") as f:
    json.dump(all_c, f)
print("saved /tmp/c364_all_sorted.json")
