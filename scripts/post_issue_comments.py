#!/usr/bin/env python3
"""Post Issue #8 evidence comments and read them back (§38 law: never claim without read-back)."""
import json, sys, urllib.request
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 8
TOKEN = Path("/home/z/.gh_token").read_text().strip()

API = "https://api.github.com"

def req(url, data=None, method="GET"):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", f"Bearer {TOKEN}")
    r.add_header("Accept", "application/vnd.github+json")
    body = json.dumps(data).encode() if data else None
    if body:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, body, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

def post_comment(md_path):
    body = Path(md_path).read_text().strip()
    status, out = req(f"{API}/repos/{REPO}/issues/{ISSUE}/comments", {"body": body}, "POST")
    if status != 201:
        print(f"POST FAIL {md_path}: http={status} {out}")
        return None
    cid = out["id"]
    url = out["html_url"]
    # read back
    rs, rb = req(f"{API}/repos/{REPO}/issues/comments/{cid}")
    ok = rs == 200 and rb.get("body", "").strip() == body
    print(f"POSTED id={cid} url={url} readback={'OK' if ok else 'MISMATCH'} ({len(body)} chars)")
    return {"id": cid, "url": url, "readback": ok}

if __name__ == "__main__":
    results = []
    for p in sys.argv[1:]:
        r = post_comment(p)
        if r:
            results.append(r)
    Path("/home/z/my-project/scripts/comment_urls.json").write_text(json.dumps(results, indent=2))
    print(f"total posted+readback: {len(results)}")
