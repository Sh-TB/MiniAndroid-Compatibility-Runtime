#!/usr/bin/env python3
"""S223: fetch issues 582/583/584/585 bodies + all comments; dump to files; print compact digest."""
import json, subprocess, sys, os

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True, cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

TOK = token()
H = {"Authorization": f"Bearer {TOK}", "Accept": "application/vnd.github+json"}
BASE = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

def curl_json(url):
    r = subprocess.run(["curl", "-sS", "-H", f"Authorization: Bearer {TOK}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)

out_dir = "/home/z/my-project/evidence/s223"
os.makedirs(out_dir, exist_ok=True)

summary = []
for num in (585, 582, 583, 584):
    issue = curl_json(f"{BASE}/issues/{num}")
    body_path = f"{out_dir}/issue_{num}_body.json"
    with open(body_path, "w") as f:
        json.dump(issue, f, indent=1)
    comments = []
    page = 1
    while True:
        batch = curl_json(f"{BASE}/issues/{num}/comments?per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        comments.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    with open(f"{out_dir}/issue_{num}_comments.json", "w") as f:
        json.dump(comments, f, indent=1)
    summary.append((num, issue.get("title", "?"), issue.get("state"), issue.get("user", {}).get("login"),
                    issue.get("created_at"), len(comments),
                    [c["id"] for c in comments[-8:]]))

for row in summary:
    print(f"#{row[0]} | {row[1][:60]} | state={row[2]} | by={row[3]} | created={row[4]} | comments={row[5]}")
    print(f"   last8 ids: {row[6]}")
