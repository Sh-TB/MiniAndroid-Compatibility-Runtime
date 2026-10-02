#!/usr/bin/env python3
"""Fetch issue #365, #364, all issues + comments + commits for forensic campaign."""
import subprocess, json, urllib.request, sys, os

out = subprocess.run(["git","credential","fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=",1)[1]
if not token:
    sys.exit("NO TOKEN")

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "forensic-campaign"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
DATA = "/home/z/my-project/forensic_data"

def api(path, dest):
    url = f"https://api.github.com{path}"
    results = []
    page = 1
    while True:
        req = urllib.request.Request(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}", headers=HDRS)
        try:
            with urllib.request.urlopen(req) as r:
                batch = json.loads(r.read())
        except Exception as e:
            print(f"ERR {path} p{page}: {e}"); break
        if not batch: break
        results.extend(batch)
        if len(batch) < 100: break
        page += 1
    with open(dest, "w") as f: json.dump(results, f, indent=1)
    print(f"OK {path}: {len(results)} items -> {dest}")
    return results

# Key issues full
for n in (365, 364):
    api(f"/repos/{REPO}/issues/{n}", f"{DATA}/issue_{n}.json")
    api(f"/repos/{REPO}/issues/{n}/comments", f"{DATA}/issue_{n}_comments.json")

# All issues list (state=all)
api(f"/repos/{REPO}/issues?state=all", f"{DATA}/issues_all.json")
# All comments on all issues
api(f"/repos/{REPO}/issues/comments", f"{DATA}/all_issue_comments.json")
# Commits
api(f"/repos/{REPO}/commits?per_page=100", f"{DATA}/commits.json")
