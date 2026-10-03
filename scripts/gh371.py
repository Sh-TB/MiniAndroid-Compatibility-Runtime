#!/usr/bin/env python3
"""Helper: read/post GitHub issue comments for the closeout."""
import subprocess, json, urllib.request, sys
from pathlib import Path

BASE = Path("/home/z/my-project")
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def _token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True, cwd=BASE).stdout
    return [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]

HDRS = {"Authorization": f"token {_token()}", "Accept": "application/vnd.github+json",
        "User-Agent": "closeout"}

def api(path, method="GET", body=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HDRS, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def issue(num):
    return api(f"issues/{num}")

def comments(num, per_page=100):
    return api(f"issues/{num}/comments?per_page={per_page}&sort=created&direction=desc")

def post_comment(num, body):
    # split into <=60000-char chunks to stay under API limit
    chunks = [body[i:i+60000] for i in range(0, len(body), 60000)]
    urls = []
    for i, c in enumerate(chunks):
        r = api(f"issues/{num}/comments", method="POST", body={"body": c})
        urls.append(r["html_url"])
    return urls

if __name__ == "__main__":
    cmd = sys.argv[1]
    num = int(sys.argv[2])
    if cmd == "view":
        it = issue(num)
        print(f"#{num} [{it['state']}] {it['title']}")
        cs = comments(num)
        print(f"comments: {len(cs)} (showing latest {min(5,len(cs))})")
        for c in cs[:5]:
            print("="*80)
            print(f"[{c['created_at']}] {c['user']['login']}  ({len(c['body'])} chars)")
            print("-"*80)
            print(c["body"][:6000])
    elif cmd == "post":
        body = open(sys.argv[3]).read()
        for u in post_comment(num, body):
            print("POSTED:", u)
