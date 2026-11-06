#!/usr/bin/env python3
"""s182_audit2.py — verify the LIVE successors of the closed 4APP block
(#494-505) + #166 close reason; finalize the audit verdicts."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s182_audit"
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    d = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True).stdout
    return [l.split("=", 1)[1] for l in d.splitlines()
            if l.startswith("password=")][0]


HDR = {"Authorization": f"token {token()}", "User-Agent": "s182-audit"}


def get(url):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=HDR)))


res = {}
for n in list(range(494, 506)) + [166]:
    iss = get(f"https://api.github.com/repos/{REPO}/issues/{n}")
    last = ""
    if iss.get("comments"):
        cs = get(iss["comments_url"] + "?per_page=100")
        if cs:
            last = (cs[-1].get("body") or "")[-400:].replace("\n", " | ")
    res[n] = {"title": iss["title"], "state": iss["state"],
              "state_reason": iss.get("state_reason"),
              "comments": iss.get("comments"),
              "updated": (iss.get("updated_at") or "")[:10],
              "last_comment_tail": last}
    print(f"#{n} [{iss['state']}/{iss.get('state_reason')}] "
          f"({iss.get('comments')} cmts, upd {res[n]['updated']}) "
          f"{iss['title'][:60]}")
    if last:
        print(f"      last: {last[:280]}")
json.dump(res, open(OUT / "successors_494_505.json", "w"), indent=1)
