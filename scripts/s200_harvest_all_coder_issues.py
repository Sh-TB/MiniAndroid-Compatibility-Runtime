#!/usr/bin/env python3
"""S200 — FULL harvest: issue bodies + ALL comments for every coder issue.
One-by-one reading basis for the achievement review + 40-task answers."""
import json, subprocess, sys, time
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200/harvest')
OUT.mkdir(parents=True, exist_ok=True)

ISSUES = [450, 490, 492, 505, 515, 519, 520, 521, 533, 536, 557, 564, 565, 566]

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
HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"

def api(url):
    for attempt in range(4):
        r = subprocess.run(["curl", "-s"] + HDRS + [url], capture_output=True, text=True)
        try:
            j = json.loads(r.stdout)
            if isinstance(j, dict) and j.get("message") and "rate limit" in j["message"].lower():
                time.sleep(20); continue
            return j
        except Exception:
            time.sleep(5)
    return {}

summary = []
for num in ISSUES:
    iss = api(f"{BASE}/issues/{num}")
    body = iss.get("body") or ""
    (OUT / f"issue_{num}_body.md").write_text(body)
    comments = []
    page = 1
    while True:
        cs = api(f"{BASE}/issues/{num}/comments?per_page=100&page={page}")
        if not isinstance(cs, list) or not cs:
            break
        comments.extend(cs)
        if len(cs) < 100:
            break
        page += 1
    allc = [{"id": c["id"], "created": c["created_at"], "user": c["user"]["login"],
             "body": c["body"]} for c in comments]
    (OUT / f"issue_{num}_comments.json").write_text(json.dumps(allc, indent=1, ensure_ascii=False))
    summary.append(f"#{num}: body={len(body)}ch comments={len(allc)} title={iss.get('title','')[:70]}")
    time.sleep(1)

print("\n".join(summary))
print("HARVEST DONE ->", OUT)
