#!/usr/bin/env python3
"""cont73_fetch_364.py — fetch issue #364 comments newest-first, print id/author/date/excerpt."""
import json
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


def api(url):
    req = urllib_request(url)


def urllib_request(url):
    import urllib.request
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token()}",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    issue = sys.argv[1] if len(sys.argv) > 1 else "364"
    per = 100
    page = 1
    comments = []
    while True:
        url = (f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
               f"?per_page={per}&page={page}&sort=created&direction=desc")
        batch = urllib_request(url)
        if not batch:
            break
        comments.extend(batch)
        if len(batch) < per:
            break
        page += 1
    print(f"TOTAL COMMENTS: {len(comments)}")
    for c in comments:
        body = c["body"].replace("\r", "")
        first = " ".join(body.split())[:220]
        print(f'--- id={c["id"]} author={c["user"]["login"]} at={c["created_at"]} len={len(body)}')
        print(f"    {first}")


if __name__ == "__main__":
    main()
