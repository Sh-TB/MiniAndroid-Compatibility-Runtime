#!/usr/bin/env python3
"""S215 batch-2 verdict posting (#520, #577, #536) — post + fetch-verify."""
import json, subprocess, sys, time, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
cred = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
TOKEN = [l.split("=",1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
        "User-Agent": "s215-verdicts-b2", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

POSTS = [(520, "v520.md"), (577, "v577b.md"), (536, "v536b.md")]
ok_all = True
for issue, fname in POSTS:
    body = open(f"/home/z/my-project/scripts/{fname}").read()
    out = api(f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
              json.dumps({"body": body}).encode(), method="POST")
    cid = out["id"]
    time.sleep(1)
    back = api(f"https://api.github.com/repos/{REPO}/issues/comments/{cid}")
    ok = back.get("body") == body
    ok_all &= ok
    print(f"posted #{issue} c={cid} len={len(body)} fetch-verified={ok}", flush=True)
sys.exit(0 if ok_all else 1)
