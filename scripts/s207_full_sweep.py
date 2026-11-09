#!/usr/bin/env python3
"""S207 — FULL paginated sweep of ALL coder + governance issues.
For each issue: fetch ALL comment pages, find my newest comment (watermark),
list every non-Sh-TB comment after it = the genuinely unreviewed wave.
Also fetch the #557 render-upload comment body for cross-check."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s207')
OUT.mkdir(parents=True, exist_ok=True)
ISSUES = [450, 492, 505, 515, 519, 520, 521, 533, 557, 566, 536, 574, 573, 570, 565]

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def gh(url):
    r = subprocess.run(["curl", "-s", "-m", "60",
                        "-H", f"Authorization: token {token()}",
                        "-H", "Accept: application/vnd.github+json",
                        url], capture_output=True, text=True)
    return json.loads(r.stdout)

def all_comments(n):
    cs, page = [], 1
    while True:
        batch = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        cs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 20:
            break
    return cs

def main():
    result, unreviewed_total = {}, 0
    for n in ISSUES:
        cs = all_comments(n)
        if not cs:
            result[n] = {"total": 0, "note": "fetch failed or empty"}
            print(f"#{n}: FETCH-FAIL")
            continue
        mine = [c for c in cs if c["user"]["login"] == "Sh-TB"]
        wm = max(mine, key=lambda c: c["id"]) if mine else None
        wm_id, wm_at = (wm["id"], wm["created_at"]) if wm else (0, "")
        newer = [c for c in cs if c["id"] > wm_id and c["user"]["login"] != "Sh-TB"]
        result[n] = {"total": len(cs), "pages_fetched": True,
                     "watermark": wm_id, "watermark_at": wm_at,
                     "unreviewed_count": len(newer),
                     "unreviewed": [{"id": c["id"], "user": c["user"]["login"],
                                     "at": c["created_at"], "len": len(c["body"]),
                                     "body": c["body"]} for c in newer]}
        unreviewed_total += len(newer)
        print(f"#{n}: total={len(cs)} watermark={wm_id}@{wm_at} unreviewed={len(newer)}")
        for c in newer:
            print(f"   -> UNREVIEWED c={c['id']} by={c['user']['login']} at={c['created_at']} len={len(c['body'])}")
    (OUT / "s207_full_sweep.json").write_text(json.dumps(result, indent=1))
    print(f"\nTOTAL UNREVIEWED: {unreviewed_total}")
    # the #557 render-upload comment body
    c = gh(f"https://api.github.com/repos/{REPO}/issues/comments/6744704882")
    body = c.get("body", "") if isinstance(c, dict) else ""
    (OUT / "s557_render_upload_body.md").write_text(body)
    print("\n== #557 render-upload comment (first 600 chars) ==")
    print(body[:600])

if __name__ == "__main__":
    main()
