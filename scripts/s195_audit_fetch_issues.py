#!/usr/bin/env python3
"""S195 AUDIT — fetch the FULL issue history (open+closed) sorted by
updated_at DESC per the MAIN CODER MASTER TASK §1. Saves the raw corpus
for the achievement inventory. Incremental partial JSON after each page
(the partial-loss law)."""
import json, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s195_audit'
OUT.mkdir(parents=True, exist_ok=True)


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
assert TOK, "no GitHub token available"
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

all_issues = []
page = 1
while True:
    r = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: token {TOK}",
         f"https://api.github.com/repos/{REPO}/issues"
         f"?state=all&per_page=100&page={page}&sort=updated&direction=desc"],
        capture_output=True, text=True)
    try:
        batch = json.loads(r.stdout)
    except Exception as e:
        print(f"page {page} parse error: {e}")
        break
    if not isinstance(batch, list) or not batch:
        break
    # keep PRs out (the API returns PRs too; an issue has no pull_request key)
    issues = [i for i in batch if 'pull_request' not in i]
    all_issues += issues
    print(f"page {page}: +{len(issues)} issues "
          f"(of {len(batch)} entries, {len(batch)-len(issues)} PRs) "
          f"total={len(all_issues)}", flush=True)
    (OUT / 'issues_raw.partial.json').write_text(json.dumps(
        {'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
         'count': len(all_issues), 'issues': all_issues}, indent=1))
    if len(batch) < 100:
        break
    page += 1
    time.sleep(0.4)

(OUT / 'issues_raw.json').write_text(json.dumps(
    {'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
     'repo': REPO, 'count': len(all_issues), 'issues': all_issues},
    indent=1))

# quick census
open_n = sum(1 for i in all_issues if i['state'] == 'open')
clos_n = len(all_issues) - open_n
nums = sorted(i['number'] for i in all_issues)
print(f"DONE: {len(all_issues)} issues ({open_n} open / {clos_n} closed), "
      f"range #{nums[0]}..#{nums[-1]}")
top = sorted(all_issues, key=lambda i: i['updated_at'], reverse=True)[:15]
for i in top:
    print(f"  #{i['number']:4d} upd={i['updated_at']} {i['state']:5s} "
          f"{(i['title'] or '')[:70]}")
