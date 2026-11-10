#!/usr/bin/env python3
"""S210 — fresh coder-progress sweep AFTER my S209 audit comments.
All authorship is under the Sh-TB account, so the watermark is ID-based:
S210_WATERMARK = 6771180657 (536_s209_audit_central, newest S209 audit id).
Any comment with id > watermark on any open thread = NEW coder progress.
Also records per-thread tail state. Output: evidence/s210/s210_sweep.json"""
import json, subprocess, sys, time
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s210')
OUT.mkdir(parents=True, exist_ok=True)
WATERMARK = 6771180657  # my S209 central audit comment id
TOP_N = 50              # recently-updated threads to scan

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
    time.sleep(0.4)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

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
    issues = gh(f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100&page=1&sort=updated&direction=desc")
    if not isinstance(issues, list):
        print("ISSUE LIST FETCH FAIL"); sys.exit(1)
    nums = [i["number"] for i in issues if "pull_request" not in i][:TOP_N]
    titles = {i["number"]: i.get("title", "") for i in issues if "pull_request" not in i}
    print(f"top-{TOP_N} recently updated:", nums)
    result = {"watermark": WATERMARK, "scanned": nums, "issues": {}}
    new_total = 0
    for n in nums:
        cs = all_comments(n)
        if not cs:
            result["issues"][n] = {"total": 0, "note": "fetch-fail-or-empty"}
            print(f"#{n}: FETCH-FAIL")
            continue
        cs.sort(key=lambda c: c["id"])
        fresh = [c for c in cs if c["id"] > WATERMARK]
        last = cs[-1]
        result["issues"][n] = {
            "title": titles.get(n, ""),
            "total": len(cs),
            "last_id": last["id"], "last_at": last["created_at"],
            "new_count": len(fresh),
            "new": [{"id": c["id"], "user": c["user"]["login"],
                     "at": c["created_at"], "len": len(c["body"]),
                     "body": c["body"]} for c in fresh]}
        new_total += len(fresh)
        flag = f" NEW={len(fresh)}" if fresh else ""
        print(f"#{n}: total={len(cs)} last={last['id']}@{last['created_at']}{flag}")
        for c in fresh:
            head = c["body"][:150].replace("\n", " | ")
            print(f"   -> NEW c={c['id']} at={c['created_at']} len={len(c['body'])}: {head}")
    (OUT / "s210_sweep.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"\nTOTAL NEW SINCE WATERMARK {WATERMARK}: {new_total}")

if __name__ == "__main__":
    main()
