#!/usr/bin/env python3
"""S207b — coverage check: for EVERY non-Sh-TB comment on coder issues in the
last 48h, verify a LATER Sh-TB comment exists on the same issue (the review
convention: my reply after their delivery). Report any coder comment with NO
later reply of mine = the true unreviewed set."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s207')
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
    gaps = []
    for n in ISSUES:
        cs = all_comments(n)
        cs.sort(key=lambda c: c["id"])
        for i, c in enumerate(cs):
            if c["user"]["login"] == "Sh-TB":
                continue
            later_mine = [m for m in cs[i+1:] if m["user"]["login"] == "Sh-TB"]
            if not later_mine:
                gaps.append({"issue": n, "id": c["id"], "user": c["user"]["login"],
                             "at": c["created_at"], "len": len(c["body"]),
                             "head": c["body"][:200]})
                print(f"GAP #{n} c={c['id']} by={c['user']['login']} at={c['created_at']}")
                print(f"     head: {c['body'][:150]!r}")
    (OUT / "s207b_coverage_gaps.json").write_text(json.dumps(gaps, indent=1))
    print(f"\nTOTAL GAPS (coder comments with no later reply from me): {len(gaps)}")

if __name__ == "__main__":
    main()
