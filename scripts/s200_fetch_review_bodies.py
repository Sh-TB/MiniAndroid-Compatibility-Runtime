#!/usr/bin/env python3
"""S200 — fetch full bodies of specific comments needing review + our pushed ones."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')

# comments to fetch in full (id -> why)
WANT = {
    6695236841: "C3 #492 S188 A24 report (tictactoe_3 FULL EXECUTION)",
    6694660722: "C8 #533 Batch 2 (batch-1 core RECONSTRUCTED, 22 rows, 99-check battery)",
    6724028268: "C4 #566 W17 addendum (worklog K-2, b5adfbd2)",
    6707480969: "C3 #557 PART 2/2 (APK table)",
    6726427444: "OURS #492 S199-close C3 feedback",
    6726426857: "OURS #557 S199-close C3 feedback",
    6726427049: "OURS #566 S199-close C4 feedback",
    6726938000: "OURS #492 targetA report",
    6727389170: "OURS #557 targetB report",
    6728642160: "OURS #557 fragpath report",
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
HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"

full = {}
for cid, why in WANT.items():
    r = subprocess.run(["curl", "-s"] + HDRS + [f"{BASE}/issues/comments/{cid}"],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        full[str(cid)] = {"why": why, "issue": j.get("issue_url", "").rsplit("/", 1)[-1],
                          "created": j.get("created_at"), "user": j.get("user", {}).get("login"),
                          "body": j.get("body", "")}
        print(f"{cid} [{why}]: issue={full[str(cid)]['issue']} len={len(j.get('body',''))}")
    except Exception as e:
        print(f"{cid}: ERROR {r.stdout[:150]}")

(OUT / "review_bodies.json").write_text(json.dumps(full, indent=2, ensure_ascii=False))
print("WROTE evidence/s200/review_bodies.json")
