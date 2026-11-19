#!/usr/bin/env python3
"""w22_fetch_issues.py — WORKSTREAM A1: recover the full issue/PR inventory.

Authenticated via `git credential fill` at runtime (token NEVER printed or
written to disk). Fetches:
  1. all issues+PRs (state=all, paginated) -> page JSON files
  2. comments for the mission-listed issues
  3. single records for the mission-listed issues + PR 626

Output: <outdir>/page_NN.json, comments_<n>.json, item_<n>.json
Progress printed as: number -> title (no bodies, no token).
"""
import json
import subprocess
import sys
import time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/w22/issues_raw"
TARGET_ISSUES = [573, 586, 597, 606, 607, 612, 620, 627, 628, 626]


def get_token():
    q = b"protocol=https\nhost=github.com\n\n"
    r = subprocess.run(["git", "credential", "fill"], input=q,
                       capture_output=True)
    tok = None
    for line in r.stdout.decode().splitlines():
        if line.startswith("password="):
            tok = line[len("password="):]
    if not tok:
        sys.exit("NO_TOKEN: credential fill returned nothing")
    return tok


def api(path, tok, params=None):
    url = "https://api.github.com%s" % path
    if params:
        url += "?" + "&".join("%s=%s" % kv for kv in params)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + tok,
        "Accept": "application/vnd.github+json",
        "User-Agent": "w22-knowledge-recovery",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 3:
                raise
            sys.stderr.write("retry %s: %s\n" % (path, e))
            time.sleep(2.0 * (attempt + 1))


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    tok = get_token()
    # 1. full inventory, paginated
    page = 1
    total = 0
    while True:
        items = api("/repos/%s/issues" % REPO, tok,
                    [("state", "all"), ("per_page", "100"),
                     ("page", str(page)), ("sort", "created"),
                     ("direction", "asc")])
        if not items:
            break
        with open("%s/page_%02d.json" % (OUT, page), "w") as f:
            json.dump(items, f)
        for it in items:
            kind = "PR" if "pull_request" in it else "I"
            print("%s%s %s" % (kind, it["number"], it["title"][:70]))
        total += len(items)
        page += 1
        time.sleep(0.15)
    print("TOTAL_ITEMS %d pages %d" % (total, page - 1))
    # 2. mission-listed items + their comments
    for n in TARGET_ISSUES:
        it = api("/repos/%s/issues/%d" % (REPO, n), tok)
        with open("%s/item_%d.json" % (OUT, n), "w") as f:
            json.dump(it, f)
        print("ITEM %d %s state=%s comments=%d pr=%s" % (
            n, it.get("title", "")[:60], it.get("state"),
            it.get("comments", 0), "pull_request" in it))
        time.sleep(0.15)
        if it.get("comments", 0) > 0 or "pull_request" in it:
            cs = api("/repos/%s/issues/%d/comments?per_page=100" % (REPO, n),
                     tok)
            with open("%s/comments_%d.json" % (OUT, n), "w") as f:
                json.dump(cs, f)
            print("COMMENTS %d -> %d" % (n, len(cs)))
            time.sleep(0.15)
    print("DONE")


if __name__ == "__main__":
    main()
