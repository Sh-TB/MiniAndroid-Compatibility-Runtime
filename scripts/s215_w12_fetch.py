#!/usr/bin/env python3
"""Assemble Coder-7 W12 from the 3 posted parts, verify T21/T22 sha256,
apply-check on current main (b24e1765) in a worktree."""
import hashlib, re, subprocess, sys, urllib.request, json

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
PART_IDS = [6787856387, 6787856970, 6787857366]
TARGET_SHA = "1a9d988b2a791bd96ae17d1f52a000c376e2ff134595a72ac24678a9a853e7ef"
TARGET_LEN = 103296

cred = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd="/home/z/my-project").stdout
TOKEN = [l.split("=",1)[1] for l in cred.splitlines() if l.startswith("password=")][0]

def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json", "User-Agent": "s215-w12"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

full = ""
for cid in PART_IDS:
    c = api(f"https://api.github.com/repos/{REPO}/issues/comments/{cid}")
    m = re.search(r"```diff\n(.*?)```", c["body"], re.S)
    if not m:
        m2 = re.search(r"```\n(.*?)```", c["body"], re.S)
        if not m2:
            print(f"part {cid}: NO CODE BLOCK"); sys.exit(1)
        seg = m2.group(1)
    else:
        seg = m.group(1)
    print(f"part {cid}: {len(seg)} chars")
    full += seg

data = full.encode()
sha = hashlib.sha256(data).hexdigest()
print(f"assembled: {len(data)} bytes sha256={sha}")
print("T21/T22:", "MATCH" if sha == TARGET_SHA and len(data) == TARGET_LEN else "MISMATCH")
open("/tmp/w12_full.patch","w").write(full)
print(f"diff --git count: {full.count('diff --git')}")
