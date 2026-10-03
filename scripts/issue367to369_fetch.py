#!/usr/bin/env python3
import subprocess, json, urllib.request, sys
out = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=",1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json", "User-Agent": "forensic"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
import os
os.makedirs("/home/z/my-project/forensic_data", exist_ok=True)
for n in (367, 368, 369):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/{n}", headers=HDRS)
    with urllib.request.urlopen(req) as r:
        obj = json.loads(r.read())
    with open(f"/home/z/my-project/forensic_data/issue_{n}.json","w") as f:
        json.dump(obj, f, indent=1)
    print("#", n, "|", obj["title"], "| state:", obj["state"], "| comments:", obj["comments"], "| created:", obj["created_at"])
    # fetch comments
    req2 = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100", headers=HDRS)
    with urllib.request.urlopen(req2) as r:
        comments = json.loads(r.read())
    with open(f"/home/z/my-project/forensic_data/issue_{n}_comments.json","w") as f:
        json.dump(comments, f, indent=1)
    print("  comments fetched:", len(comments))
