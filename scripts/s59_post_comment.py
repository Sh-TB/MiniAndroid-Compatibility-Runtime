#!/usr/bin/env python3
"""s59_post_comment.py <issue_number> <comment_md_path> — post a GitHub issue comment."""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


def main():
    n = sys.argv[1]
    body = open(sys.argv[2]).read()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{n}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {token()}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
        print(f"posted #{n}: {d['html_url']}")


if __name__ == "__main__":
    main()
