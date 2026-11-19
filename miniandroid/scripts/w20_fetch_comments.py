#!/usr/bin/env python3
"""W20-P1: fetch the independent coder's comments (#612 7002388310/7002484385,
#627 7002388704/7002484807) and list recent issues for context."""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
IDS = {"#612/7002388310": ("issues/612/comments", 7002388310),
       "#612/7002484385": ("issues/612/comments", 7002484385),
       "#627/7002388704": ("issues/627/comments", 7002388704),
       "#627/7002484807": ("issues/627/comments", 7002484807)}

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}

outdir = "evidence/w20"
for key, (path, cid) in IDS.items():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}", headers=HDRS)
    with urllib.request.urlopen(req) as r:
        comments = json.loads(r.read())
    match = [c for c in comments if c["id"] == cid]
    if not match:
        print(f"{key}: NOT FOUND ({len(comments)} comments scanned)")
        continue
    body = match[0]["body"]
    fn = f"{outdir}/coder_{cid}.md"
    with open(fn, "w") as fh:
        fh.write(body)
    print(f"{key}: {len(body)} chars -> {fn} (user {match[0]['user']['login']})")
