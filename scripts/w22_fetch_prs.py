#!/usr/bin/env python3
"""w22_fetch_prs.py — PR 625/626 details: merged_at, base, head, files, patch."""
import json
import os
import subprocess
import time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/w22/issues_raw"


def get_token():
    q = b"protocol=https\nhost=github.com\n\n"
    r = subprocess.run(["git", "credential", "fill"], input=q,
                       capture_output=True)
    for line in r.stdout.decode().splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise SystemExit("NO_TOKEN")


def api(path, tok):
    url = "https://api.github.com%s" % path
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + tok,
        "Accept": "application/vnd.github+json",
        "User-Agent": "w22-knowledge-recovery",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


tok = get_token()
for pr in (625, 626):
    meta = api("/repos/%s/pulls/%d" % (REPO, pr), tok)
    with open("%s/pr_%d.json" % (OUT, pr), "w") as f:
        json.dump(meta, f)
    print("PR%d merged=%s state=%s base=%s head=%s/%s@%s files=%s" % (
        pr, meta.get("merged_at"), meta.get("state"),
        meta["base"]["ref"], meta["head"]["repo"]["full_name"],
        meta["head"]["ref"], meta["head"]["sha"][:10], meta.get("changed_files")))
    time.sleep(0.2)
    files = api("/repos/%s/pulls/%d/files?per_page=100" % (REPO, pr), tok)
    with open("%s/pr_%d_files.json" % (OUT, pr), "w") as f:
        json.dump(files, f)
    for fe in files:
        print("  %s +%d -%d" % (fe["filename"], fe["additions"], fe["deletions"]))
    time.sleep(0.2)
print("DONE")
