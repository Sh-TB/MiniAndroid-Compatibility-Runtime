#!/usr/bin/env python3
"""S225: fetch issues 582-585 (+ any newer) bodies and all comments; detect edits (updated_at > created_at)."""
import json, subprocess, os

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/s225"
os.makedirs(OUT, exist_ok=True)

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
H = ["-H", f"Authorization: token {TOK}"]

def api(url):
    r = subprocess.run(["curl", "-s", "--max-time", "60"] + H + [url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception as e:
        return {"_error": str(e), "_raw": r.stdout[:200]}

# 1) all issues >= 582 (state all)
issues = []
for p in range(1, 6):
    data = api(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={p}&sort=created&direction=desc")
    if not isinstance(data, list) or not data:
        break
    issues += data
    if data[-1]["number"] < 582:
        break

mine = [i for i in issues if i["number"] >= 582 and "pull_request" not in i]
mine.sort(key=lambda i: i["number"])
print("ISSUES >=582:", [(i["number"], i["state"], i["updated_at"], i["comments"]) for i in mine])

result = {}
for it in mine:
    n = it["number"]
    body = it.get("body") or ""
    cs = []
    for p in range(1, 40):
        data = api(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={p}")
        if not isinstance(data, list) or not data:
            break
        cs += data
        if len(data) < 100:
            break
    cs.sort(key=lambda c: c["id"])
    edited = [c for c in cs if c.get("updated_at") and c.get("created_at") and c["updated_at"] > c["created_at"]]
    result[n] = {
        "title": it["title"], "state": it["state"], "body": body,
        "author": it["user"]["login"], "created": it["created_at"], "updated": it["updated_at"],
        "n_comments": len(cs),
        "comments": [{"id": c["id"], "user": c["user"]["login"], "created": c["created_at"],
                      "updated": c.get("updated_at"), "edited": c["id"] in {e["id"] for e in edited},
                      "body": c["body"]} for c in cs],
        "edited_count": len(edited),
    }
    print(f"#{n}: {len(cs)} comments, {len(edited)} edited")

with open(f"{OUT}/issues_582plus.json", "w") as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
print("saved", f"{OUT}/issues_582plus.json")
