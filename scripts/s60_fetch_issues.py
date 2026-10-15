#!/usr/bin/env python3
"""s60_fetch_issues.py — fetch ALL open issues (paginated) with bodies into run/s60/issues_all.json.
Also records total count across pages (pagination-proof) and recently-closed issues (for reconciliation)."""
import json
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/run/s60/issues_all.json"


def gh(url):
    r = subprocess.run(["bash", "/home/z/my-project/scripts/gh_api.sh", url],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit(f"gh_api failed: {r.stderr[:300]}")
    return json.loads(r.stdout)


def main():
    issues = []
    page = 1
    while True:
        batch = gh(f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100&page={page}")
        if not batch:
            break
        issues.extend(batch)
        print(f"page {page}: +{len(batch)}", file=sys.stderr)
        if len(batch) < 100:
            break
        page += 1
    # keep only true issues (drop PRs)
    issues = [i for i in issues if "pull_request" not in i]
    slim = [{
        "number": i["number"], "title": i["title"], "state": i["state"],
        "labels": [l["name"] for l in i["labels"]],
        "created": i["created_at"], "updated": i["updated_at"],
        "comments": i["comments"], "body": (i.get("body") or ""),
    } for i in issues]
    slim.sort(key=lambda x: x["number"])
    json.dump(slim, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"TOTAL open issues: {len(slim)} (range #{slim[0]['number']}..#{slim[-1]['number']}) -> {OUT}")

    # closed-since reconciliation reference: recently closed (top 30 by update)
    closed = gh(f"https://api.github.com/repos/{REPO}/issues?state=closed&per_page=30&sort=updated&direction=desc")
    cl = [{"number": i["number"], "title": i["title"], "closed_at": i["closed_at"],
           "state_reason": i.get("state_reason")} for i in closed if "pull_request" not in i]
    json.dump(cl, open("/home/z/my-project/run/s60/recently_closed.json", "w"), indent=1)
    print(f"recently closed sampled: {len(cl)}")


if __name__ == "__main__":
    main()
