#!/usr/bin/env python3
"""S116: strip Persian text from the 7 legacy evidence comments (English-only directive).
Drops every line containing Persian characters, collapses blank runs, PATCHes back."""
import json
import re
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = open("/tmp/.gh_token").read().strip()
BASE = f"https://api.github.com/repos/{REPO}"
PERSIAN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        body = r.read().decode()
        return json.loads(body) if body else None


IDS = [5857414802, 5858470298, 5858906111, 5859831075, 5857414959, 5857415062, 5857497464]
for cid in IDS:
    c = api("GET", f"{BASE}/issues/comments/{cid}")
    body = c["body"]
    lines = [l for l in body.split("\n") if not PERSIAN.search(l)]
    # drop a dangling horizontal rule left behind by the removal
    while lines and lines[-1].strip() in ("", "---"):
        lines.pop()
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)  # collapse blank runs
    assert not PERSIAN.search(out), f"persian still present in {cid}"
    api("PATCH", f"{BASE}/issues/comments/{cid}", {"body": out})
    print(f"{cid}: {len(body)} -> {len(out)} chars, persian stripped")
print("done")
