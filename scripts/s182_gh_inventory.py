#!/usr/bin/env python3
"""s182_gh_inventory.py — fetch ALL issues (open+closed) from the campaign repo.

Answers the user's «115 مورد بسته شده» claim precisely: how many issues are
closed, how many open, split app/game vs infra. Saves evidence/s182_audit/.
"""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s182_audit"
OUT.mkdir(parents=True, exist_ok=True)
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    d = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True).stdout
    return [l.split("=", 1)[1] for l in d.splitlines()
            if l.startswith("password=")][0]


TOK = token()
HDR = {"Authorization": f"token {TOK}", "User-Agent": "s182-audit"}


def get(url):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=HDR))
    return json.load(r), r.headers


def fetch_all(kind):
    rows, page = [], 1
    while True:
        u = (f"https://api.github.com/repos/{REPO}/issues?state={kind}"
             f"&per_page=100&page={page}&sort=created&direction=asc")
        chunk, hdr = get(u)
        rows.extend(chunk)
        link = hdr.get("Link") or ""
        if 'rel="next"' not in link or not chunk:
            break
        page += 1
    return rows


allrows = fetch_all("all")
issues = [r for r in allrows if "pull_request" not in r]
prs = [r for r in allrows if "pull_request" in r]
open_i = [r for r in issues if r["state"] == "open"]
closed_i = [r for r in issues if r["state"] == "closed"]
open_p = [r for r in prs if r["state"] == "open"]
closed_p = [r for r in prs if r["state"] == "closed"]

slim = [{"n": r["number"], "title": r["title"], "state": r["state"],
         "closed_at": r.get("closed_at"), "created_at": r.get("created_at"),
         "labels": [l["name"] for l in r.get("labels", [])],
         "is_pr": "pull_request" in r}
        for r in allrows]
json.dump(slim, open(OUT / "issues_all.json", "w"), indent=1)

print(f"issues: open={len(open_i)} closed={len(closed_i)} total={len(issues)}")
print(f"prs:    open={len(open_p)} closed={len(closed_p)} total={len(prs)}")
print("\nclosed issues by number span:",
      f"min #{min(r['number'] for r in closed_i)} .. "
      f"max #{max(r['number'] for r in closed_i)}")
# keyword split: app/game-tracker vs infra
import re
appish = [r for r in closed_i if re.search(
    r"APP|GAME|CONT-|4APP|APK|Telegram|Dooz|dooz|Tusky|Thunderbird|"
    r"Nextcloud|Forkgram|titl", r["title"], re.I)]
print(f"closed that look app/game related: {len(appish)}")
print("\nNEWEST 25 closed issues:")
for r in sorted(closed_i, key=lambda x: -(x["number"])):
    print(f"  #{r['number']:4d} {r['closed_at'][:10] if r.get('closed_at') else '?'} {r['title'][:70]}")
