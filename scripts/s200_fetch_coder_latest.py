#!/usr/bin/env python3
"""S200 — fetch the LATEST coder comments per issue (since our last push round)
so we can review their newest achievements before posting the next feedback."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')

ISSUES = [450, 490, 492, 557, 566, 505, 515, 519, 520, 521, 533, 536]
# our last push timestamps per issue (from posted_comment_ids.json)
LAST_OURS = {
    450: "2026-11-08T00:00:00Z", 505: "2026-11-08T00:00:00Z",
    515: "2026-11-08T00:00:00Z", 520: "2026-11-08T00:00:00Z",
    519: "2026-11-08T00:00:00Z", 536: "2026-11-08T00:00:00Z",
    492: "2026-11-08T00:00:00Z", 557: "2026-11-08T00:00:00Z",
    566: "2026-11-08T00:00:00Z", 521: "2026-11-08T00:00:00Z",
    533: "2026-11-08T00:00:00Z", 490: "2026-11-08T00:00:00Z",
}

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
if not TOK:
    sys.exit("NO TOKEN")

HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"

result = {}
for num in ISSUES:
    r = subprocess.run(["curl", "-s"] + HDRS +
                       [f"{BASE}/issues/{num}/comments?per_page=100&sort=created&direction=desc"],
                       capture_output=True, text=True)
    try:
        comments = json.loads(r.stdout)
    except Exception:
        comments = []
    if not isinstance(comments, list):
        result[num] = {"error": str(comments)[:200]}
        continue
    result[num] = {
        "count": len(comments),
        "latest": [
            {"id": c["id"], "user": c["user"]["login"],
             "created": c["created_at"],
             "body_head": c["body"][:1500]}
            for c in comments[:6]
        ],
    }

(OUT / "coder_latest_comments.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

# console summary: newest comment per issue
for num in ISSUES:
    if "error" in result[num]:
        print(f"#{num}: ERROR {result[num]['error']}")
        continue
    lat = result[num]["latest"]
    if lat:
        print(f"#{num}: {result[num]['count']} fetched | NEWEST id={lat[0]['id']} by {lat[0]['user']} at {lat[0]['created']}")
    else:
        print(f"#{num}: no comments")
