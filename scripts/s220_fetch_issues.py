#!/usr/bin/env python3
"""S220: fetch issues #582, #583, #584 full bodies + all comments."""
import json, subprocess, os, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = None
r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                   capture_output=True, text=True, cwd="/home/z/my-project")
for line in r.stdout.splitlines():
    if line.startswith("password="):
        TOKEN = line.split("=", 1)[1]

API = f"https://api.github.com/repos/{REPO}"

def gh(url):
    """GET with pagination. Handles both dict (single object) and list responses."""
    out = []
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        cmd = ["curl", "-sS", "-H", f"Authorization: token {TOKEN}",
               "-H", "Accept: application/vnd.github+json",
               f"{url}{sep}per_page=100&page={page}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        try:
            batch = json.loads(r.stdout)
        except Exception as e:
            print(f"ERR parsing page {page} of {url}: {e}", file=sys.stderr)
            break
        if isinstance(batch, dict):
            if "message" in batch:
                print(f"API msg for {url}: {batch['message']}", file=sys.stderr)
            return batch
        if not isinstance(batch, list) or len(batch) == 0:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out

results = {}
for num in (582, 583, 584):
    issue = gh(f"{API}/issues/{num}")
    comments = gh(f"{API}/issues/{num}/comments")
    results[num] = {"issue": issue, "comments": comments}
    print(f"#{num}: title={issue.get('title','?')[:80]!r} comments={len(comments)} state={issue.get('state')}")
    for c in comments:
        print(f"  - id={c['id']} {c['user']['login']} at={c['created_at']} upd={c['updated_at']} len={len(c['body'])}")

with open("/home/z/my-project/forensic_data/s220_issues.json", "w") as f:
    json.dump(results, f, indent=1)
print("saved -> forensic_data/s220_issues.json")
