#!/usr/bin/env python3
"""S188: post the master directive + rules + phase issues so all Coders must read them."""
import subprocess, json, urllib.request, sys, time

sys.path.insert(0, "/home/z/my-project/scripts")
from s188_issues_data import ISSUES_PART1
from s188_issues_data2 import ISSUES_PART2

out = subprocess.run(["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s188-directive"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def api(path, body=None, method="GET"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"https://api.github.com{path}",
        data=data, headers=HDRS, method=method)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

# 1) existing issues (dedup): all open+closed, titles containing "[S188"
existing = {}
page = 1
while True:
    batch = api(f"/repos/{REPO}/issues?state=all&per_page=100&page={page}&sort=created&direction=desc")
    if not batch:
        break
    for it in batch:
        if "[S188" in it.get("title", ""):
            existing[it["title"]] = it["number"]
    if len(batch) < 100:
        break
    page += 1
print(f"existing S188 issues: {existing or 'none'}")

# 2) post in order
posted = []
master_no = None
for item in ISSUES_PART1 + ISSUES_PART2:
    if item["title"] in existing:
        print(f"SKIP (exists #{existing[item['title']]}): {item['title'][:70]}")
        if master_no is None:
            master_no = existing[item["title"]]  # first in list = master
        continue
    iss = api(f"/repos/{REPO}/issues", {"title": item["title"], "body": item["body"],
                                        "labels": item["labels"]}, method="POST")
    posted.append(iss["number"])
    print(f"POSTED #{iss['number']}: {iss['title'][:80]}")
    if master_no is None:
        master_no = iss["number"]
    time.sleep(1)

# 3) cross-reference comments on governing trackers
if master_no:
    note = (f"S188 master directive is now binding: **#{master_no}** "
            f"(full text: `docs/S188_DIRECTIVE.md` on main). "
            f"Every Coder 2\u20139 must read it and comment `ACK S188` there. "
            f"Phase issues are linked from the master issue. "
            f"First milestone: \u22655 small apps/games with real application-owned graphical "
            f"interfaces on ONE integrated binary \u2014 UNOBSERVED is never PASS.")
    for target in (536, 492):
        try:
            api(f"/repos/{REPO}/issues/{target}/comments", {"body": note}, method="POST")
            print(f"cross-ref posted on #{target}")
            time.sleep(1)
        except Exception as e:
            print(f"cross-ref #{target} failed: {e}")

print("DONE", {"posted": posted, "master": master_no})
