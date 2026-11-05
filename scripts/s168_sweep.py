#!/usr/bin/env python3
"""s168_sweep.py — S168 coder sweep: issues by updated_at, find new
deliverables (inline diffs) since the S167 sweep watermark
(2026-11-04T23:48Z). Law: claims without artifacts = zero value."""
import json
import os
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
WATERMARK = "2026-11-04T23:48:00Z"


def token():
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n",
                       capture_output=True, text=True, cwd="/home/z/my-project")
    for line in r.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def gh(url):
    tk = token()
    cmd = ["curl", "-sS", "-H", "Accept: application/vnd.github+json"]
    if tk:
        cmd += ["-H", f"Authorization: Bearer {tk}"]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)


def main():
    issues = gh(f"https://api.github.com/repos/{REPO}/issues"
                f"?state=all&sort=updated&direction=desc&per_page=40")
    if not isinstance(issues, list):
        print("API ERROR:", json.dumps(issues)[:400])
        sys.exit(1)
    new = []
    print(f"{'issue':>6} {'updated':<20} {'comments':>8} state  title")
    for it in issues:
        pr = "pull_request" in it
        print(f"{it['number']:>6} {it['updated_at']:<20} "
              f"{it['comments']:>8} {it['state']:<6} "
              f"{it['title'][:60]}{' [PR]' if pr else ''}")
        if it["updated_at"] > WATERMARK:
            new.append(it["number"])
    print("\nNEW since watermark:", new or "NONE")
    # pull comment bodies for every NEW issue; flag inline diff payloads
    for n in new:
        cs = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments"
                f"?per_page=30&sort=created&direction=desc")
        if not isinstance(cs, list):
            continue
        for c in cs:
            body = c.get("body") or ""
            has_diff = ("diff --git" in body) or ("--- a/" in body) or \
                       ("+++ b/" in body)
            print(f"  #{n} comment {c['id']} by {c['user']['login']} "
                  f"{c['created_at']} len={len(body)} inline_diff={has_diff}")


if __name__ == "__main__":
    main()
