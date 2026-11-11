#!/usr/bin/env python3
"""Fetch specific issue comments + list #520 part comments for C7 reassembly."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def token():
    out = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project/miniandroid",
                         input="protocol=https\nhost=github.com\n", capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

TOK = token()

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

def fetch_all_comments(issue_no):
    out, page = [], 1
    while True:
        batch = api(f"https://api.github.com/repos/{REPO}/issues/{issue_no}/comments?per_page=100&page={page}")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out

if sys.argv[1] == "c8":
    # find the C8 batch-4 delivery comment on #533 (before my receipt 6777808501)
    cs = fetch_all_comments(533)
    for c in cs:
        if c["id"] < 6777808501 and c["user"]["login"] != "Sh-TB":
            b = c.get("body") or ""
            if "batch-4" in b.lower() or "35" in b:
                print(f"=== #{533} c={c['id']} @{c['user']['login']} {c['created_at']} len={len(b)} ===")
                print(b[:1500])
                print("...TRUNC" if len(b) > 1500 else "")
elif sys.argv[1] == "c7":
    cs = fetch_all_comments(520)
    # list all coder comments with length; identify part carriers (big comments with diff fences)
    for c in cs:
        b = c.get("body") or ""
        fences = b.count("````")
        print(f"c={c['id']} @{c['user']['login']} {c['created_at']} len={len(b)} 4fence={fences} head={b[:80]!r}")
