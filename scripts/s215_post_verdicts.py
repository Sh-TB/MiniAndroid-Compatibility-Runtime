#!/usr/bin/env python3
"""S215 verdict posting — reads the 6 verdict .md files, posts, verifies by re-fetch."""
import json, subprocess, sys, urllib.request, time

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
cred = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
TOKEN = [l.split("=",1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
        "User-Agent": "s215-verdicts", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

POSTS = [(581, "v581.md"), (577, "v577.md"), (519, "v519.md"),
         (570, "v570.md"), (573, "v573.md"), (536, "v536.md")]

results = []
for issue, fname in POSTS:
    body = open(f"/home/z/my-project/scripts/{fname}").read()
    out = api(f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
              json.dumps({"body": body}).encode(), method="POST")
    cid = out["id"]
    time.sleep(1)
    back = api(f"https://api.github.com/repos/{REPO}/issues/comments/{cid}")
    ok = (back.get("body") == body)
    results.append((issue, cid, len(body), ok))
    print(f"posted #{issue} c={cid} len={len(body)} fetch-verified={ok}", flush=True)

print("\nSUMMARY")
for issue, cid, l, ok in results:
    print(f"#{issue} c={cid} verified={ok}")
bad = [r for r in results if not r[3]]
sys.exit(1 if bad else 0)
