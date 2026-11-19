#!/usr/bin/env python3
"""W19-8: locate the issue/thread that tracks the P0 blocker (audit #627
C-02 / dalvik_bridge mega-TU). GET-only, no posting."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=30"
    f"&sort=updated", headers=HDRS)
with urllib.request.urlopen(req) as r:
    items = json.loads(r.read())
for it in items:
    n = it['number']
    title = it['title'][:76]
    if any(k in title.lower() for k in
           ['p0', '627', 'bridge', 'split', 'audit', 'dalvik_bridge', '612']):
        print(f"#{n} [{it['state']}] {title}")
