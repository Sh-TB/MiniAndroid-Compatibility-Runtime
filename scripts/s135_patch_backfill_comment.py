#!/usr/bin/env python3
"""S135: PATCH the BACKFILL-HEADER comment on issue #354 with the corrected commit list."""
import json
import subprocess
import sys
import urllib.request

sys.path.insert(0, "/home/z/my-project/scripts")
from s135_comment_bodies import COMMENTS

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
COMMENT_ID = 5935845159
URL = f"https://api.github.com/repos/{REPO}/issues/comments/{COMMENT_ID}"


def gh_token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd="/home/z/my-project",
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise RuntimeError("no token")


def main():
    token = gh_token()
    body = next(c["body"] for c in COMMENTS if c["key"] == "BACKFILL-HEADER")
    r = urllib.request.Request(URL, method="PATCH")
    r.add_header("Authorization", f"token {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "miniandroid-campaign")
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, json.dumps({"body": body}).encode()) as resp:
        d = json.loads(resp.read().decode())
    print(f"PATCHED comment {d['id']} at {d['html_url']} (edited: {d['edited']})")


if __name__ == "__main__":
    main()
