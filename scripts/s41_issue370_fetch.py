#!/usr/bin/env python3
"""Fetch Issue #370 body + comments for the INSTALL-ENVIRONMENT CAPABILITY GATE program."""
import subprocess, json, urllib.request, os

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
token = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "forensic"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
os.makedirs("/home/z/my-project/forensic_data", exist_ok=True)

req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/370", headers=HDRS)
with urllib.request.urlopen(req) as r:
    obj = json.loads(r.read())
with open("/home/z/my-project/forensic_data/issue_370.json", "w") as f:
    json.dump(obj, f, indent=1)
print("# 370 |", obj["title"], "| state:", obj["state"], "| comments:", obj["comments"],
      "| created:", obj["created_at"])

req2 = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/370/comments?per_page=100", headers=HDRS)
with urllib.request.urlopen(req2) as r:
    comments = json.loads(r.read())
with open("/home/z/my-project/forensic_data/issue_370_comments.json", "w") as f:
    json.dump(comments, f, indent=1)
print("  comments fetched:", len(comments))
