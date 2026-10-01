#!/usr/bin/env python3
"""S135: publish S130..S135 achievement comments to GitHub issue #354 (idempotent)."""
import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, "/home/z/my-project/scripts")
from s135_comment_bodies import COMMENTS

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 354
API = f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments"


def gh_token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd="/home/z/my-project",
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise RuntimeError("no token from git credential fill")


def req(url, token, data=None, method=None):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", f"token {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "miniandroid-campaign")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, body) as resp:
        return json.loads(resp.read().decode())


def main():
    token = gh_token()
    existing = req(f"{API}?per_page=100", token)
    existing_headers = {c["body"].split("\n")[0] for c in existing}
    posted, skipped = [], []
    for c in COMMENTS:
        first_line = c["body"].split("\n")[0]
        if first_line in existing_headers:
            skipped.append(c["key"])
            print(f"SKIP (exists): {c['key']}")
            continue
        created = req(API, token, data={"body": c["body"]}, method="POST")
        posted.append(c["key"])
        print(f"POSTED {c['key']}: id={created['id']} url={created['html_url']}")
        time.sleep(1.0)
    print(f"DONE posted={len(posted)} skipped={len(skipped)}")


if __name__ == "__main__":
    main()
