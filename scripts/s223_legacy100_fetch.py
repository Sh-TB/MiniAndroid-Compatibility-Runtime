#!/usr/bin/env python3
"""S223/#585: fetch the 100 oldest OPEN issues + the GAME-series states; dump JSON for the audit ledger."""
import json, subprocess, os

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True, cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
out_dir = "/home/z/my-project/evidence/s223/legacy100"
os.makedirs(out_dir, exist_ok=True)

def curl_json(url):
    r = subprocess.run(["curl", "-sS", "-H", f"Authorization: Bearer {TOK}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)

# search API: 100 oldest open issues
issues = []
page = 1
while len(issues) < 100:
    q = f"https://api.github.com/search/issues?q=repo:{REPO}+is:issue+is:open&sort=created&order=asc&per_page=100&page={page}"
    res = curl_json(q)
    items = res.get("items", [])
    if not items:
        break
    issues.extend(items)
    page += 1
    if page > 3:
        break

issues = issues[:100]
print(f"oldest-open fetched: {len(issues)}; first=#{issues[0]['number']} last=#{issues[-1]['number']}")

# full detail for each (body needed for state evidence)
detail = []
for it in issues:
    num = it["number"]
    full = curl_json(f"https://api.github.com/repos/{REPO}/issues/{num}")
    detail.append({
        "number": num,
        "title": full.get("title", "")[:160],
        "state": full.get("state"),
        "labels": [l["name"] for l in full.get("labels", [])],
        "created_at": full.get("created_at"),
        "updated_at": full.get("updated_at"),
        "comments": full.get("comments"),
        "body": (full.get("body") or "")[:4000],
    })

with open(f"{out_dir}/oldest_open_100.json", "w") as f:
    json.dump(detail, f, indent=1)
print("saved oldest_open_100.json")
for d in detail[:12]:
    print(f"#{d['number']} [{','.join(d['labels'][:3])}] {d['title'][:70]} (upd {d['updated_at'][:10]}, {d['comments']}c)")
