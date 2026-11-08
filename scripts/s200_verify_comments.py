#!/usr/bin/env python3
"""S200 step 0 — GROUND TRUTH on GitHub comments.
Verify the 4 comment IDs claimed at S199 close actually exist, and fetch
the latest comment per coder issue so we know exactly what is MISSING
before posting anything. Partial-loss law: writes incremental JSON."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')
OUT.mkdir(parents=True, exist_ok=True)

CLAIMED = [6726426857, 6726427049, 6726427227, 6726427444]
# candidate issue homes per coder (from s195 audit priority list)
ISSUES = {
    492: "C3 S196/S198 verdict thread",
    557: "C3 S196/S198c verdict",
    566: "C4 W17 F-C4-631 intake",
    521: "C9 npTc",
    519: "C? (coder7/8/9 group)",
    520: "C? (coder7/8/9 group)",
    533: "C? (coder7/8/9 group)",
    505: "C2 candidate",
    450: "C2 candidate",
    490: "C2 candidate",
    515: "C6 candidate",
    536: "central tracker",
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
    sys.exit("NO TOKEN — cannot verify or post")

HDRS = ["-H", f"Authorization: token {TOK}",
        "-H", "Accept: application/vnd.github+json"]
BASE = f"https://api.github.com/repos/{REPO}"

res = {"claimed_comments": {}, "issues": {}}

for cid in CLAIMED:
    r = subprocess.run(["curl", "-s"] + HDRS + [f"{BASE}/issues/comments/{cid}"],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {"error": r.stdout[:200]}
    if "id" in j:
        res["claimed_comments"][str(cid)] = {
            "exists": True, "issue_url": j.get("issue_url"),
            "created_at": j.get("created_at"),
            "body_head": (j.get("body") or "")[:150],
        }
        print(f"comment {cid}: EXISTS on issue "
              f"{j.get('issue_url', '').split('/')[-1]} "
              f"({j.get('created_at')})")
    else:
        res["claimed_comments"][str(cid)] = {"exists": False, "raw": str(j)[:200]}
        print(f"comment {cid}: MISSING / {str(j)[:120]}")

for n, label in ISSUES.items():
    r = subprocess.run(["curl", "-s"] + HDRS + [f"{BASE}/issues/{n}"],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {}
    title = j.get("title", "?")
    ncom = j.get("comments", "?")
    # last comment
    r2 = subprocess.run(["curl", "-s"] + HDRS +
                        [f"{BASE}/issues/{n}/comments?per_page=3"],
                        capture_output=True, text=True)
    try:
        cs = json.loads(r2.stdout)
        last = cs[-1] if cs else None
        lastinfo = {"id": last["id"], "at": last["created_at"],
                    "head": (last["body"] or "")[:100]} if last else None
    except Exception:
        lastinfo = None
    res["issues"][str(n)] = {"title": title, "comments": ncom,
                             "state": j.get("state"), "last": lastinfo}
    print(f"#{n} [{label}]: '{title}' comments={ncom} "
          f"last={lastinfo['id'] if lastinfo else 'NONE'}")

(OUT / "verify_ground_truth.json").write_text(json.dumps(res, indent=1))
print("WROTE", OUT / "verify_ground_truth.json")
