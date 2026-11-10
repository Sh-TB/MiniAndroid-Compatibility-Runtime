#!/usr/bin/env python3
"""S208 — forward sweep: ALL open issues (catch new ones) + full unreviewed
extraction per issue (paginated, watermark = newest Sh-TB comment).
Output: evidence/s208/s208_sweep.json + per-comment bodies for review."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s208')
OUT.mkdir(parents=True, exist_ok=True)

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
        if page > 25:
            break
    return cs

def main():
    # 1) all open issues
    issues, page = [], 1
    while True:
        batch = gh(f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100&page={page}&sort=updated&direction=desc")
        if not isinstance(batch, list) or not batch:
            break
        issues.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 10:
            break
    nums = [i["number"] for i in issues if "pull_request" not in i]
    print(f"open issues: {len(nums)} -> {nums}")
    result, unrev_total = {"open_issues": nums, "issues": {}}, 0
    for n in nums:
        cs = all_comments(n)
        if not cs:
            result["issues"][n] = {"total": 0, "note": "fetch-fail-or-empty"}
            print(f"#{n}: FETCH-FAIL")
            continue
        mine = [c for c in cs if c["user"]["login"] == "Sh-TB"]
        wm = max(mine, key=lambda c: c["id"]) if mine else None
        wm_id, wm_at = (wm["id"], wm["created_at"]) if wm else (0, "")
        newer = [c for c in cs if c["id"] > wm_id and c["user"]["login"] != "Sh-TB"]
        result["issues"][n] = {"total": len(cs), "watermark": wm_id,
                               "watermark_at": wm_at,
                               "unreviewed_count": len(newer),
                               "unreviewed": [{"id": c["id"],
                                               "user": c["user"]["login"],
                                               "at": c["created_at"],
                                               "len": len(c["body"]),
                                               "body": c["body"]} for c in newer]}
        unrev_total += len(newer)
        print(f"#{n}: total={len(cs)} wm={wm_id}@{wm_at} unrev={len(newer)}")
        for c in newer:
            print(f"   -> UNREVIEWED c={c['id']} by={c['user']['login']} at={c['created_at']} len={len(c['body'])}")
    (OUT / "s208_sweep.json").write_text(json.dumps(result, indent=1))
    print(f"\nTOTAL UNREVIEWED ACROSS ALL OPEN ISSUES: {unrev_total}")

if __name__ == "__main__":
    main()
