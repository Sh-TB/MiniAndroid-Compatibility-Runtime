#!/usr/bin/env python3
"""cont114_post_comment.py — post a markdown file as an issue comment
(git-credential token path; run/.ghtoken does not exist in this container)."""
import json, subprocess, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    return [l.split("=", 1)[1] for l in out.splitlines()
            if l.startswith("password=")][0]

def main():
    issue = int(sys.argv[1])
    body = open(sys.argv[2]).read()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {token()}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "forensic"})
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    print("posted comment id:", resp["id"], "url:", resp["html_url"])

if __name__ == "__main__":
    main()
