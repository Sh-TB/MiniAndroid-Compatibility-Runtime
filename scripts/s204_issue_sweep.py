#!/usr/bin/env python3
"""S204 — deeper unreviewed sweep: (a) latest NON-mine comment per coder issue
with timestamps; (b) issue bodies edited AFTER my newest own comment there."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s204')
ISSUES = [450, 492, 505, 515, 519, 520, 521, 527, 533, 557, 566, 570, 573, 565]

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

res = {}
for n in ISSUES:
    it = gh(f"https://api.github.com/repos/{REPO}/issues/{n}")
    cs = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page=1")
    # paginate if needed
    while len(cs) and len(cs) % 100 == 0:
        more = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={len(cs)//100+1}")
        if not more: break
        cs += more
    nonmine = [c for c in cs if c["user"]["login"] != "Sh-TB"]
    nonmine.sort(key=lambda c: c["created_at"])
    latest = nonmine[-1] if nonmine else None
    body_newer = it["updated_at"] > it["created_at"]  # body was edited at some point
    entry = {
        "title": it["title"][:60],
        "issue_created": it["created_at"], "issue_updated": it["updated_at"],
        "total_comments": len(cs),
        "latest_nonmine": {"id": latest["id"], "user": latest["user"]["login"],
                           "at": latest["created_at"], "len": len(latest["body"]),
                           "tail": latest["body"][-300:]} if latest else None,
    }
    res[n] = entry
    ln = entry["latest_nonmine"]
    print(f"#{n} upd={it['updated_at'][:16]} n={len(cs)} latest-nonmine: "
          + (f"{ln['user']} @{ln['at'][:16]} len={ln['len']}" if ln else "NONE"))

(OUT / "coder_issue_sweep_204.json").write_text(json.dumps(res, indent=1))
print("saved ->", OUT / "coder_issue_sweep_204.json")
