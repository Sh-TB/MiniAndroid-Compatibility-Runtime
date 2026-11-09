#!/usr/bin/env python3
"""S204 — fetch ALL comments on the coder issues, find everything posted
AFTER our newest own comment on each issue (= the unreviewed wave), save the
full bodies for review. Also list issues updated since the last 3 days."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s204')
ISSUES = [450, 492, 505, 515, 519, 520, 521, 533, 557, 566]

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

def main():
    me = gh("https://api.github.com/user")
    login = me.get("login", "?")
    print(f"my login: {login}")
    result = {}
    for n in ISSUES:
        cs = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100")
        mine = [c for c in cs if c["user"]["login"] == login]
        wm_id, wm_at = (max(mine, key=lambda c: c["id"])["id"],
                        max(mine, key=lambda c: c["id"])["created_at"]) if mine else (None, None)
        newer = [c for c in cs if wm_at and c["created_at"] > wm_at and c["user"]["login"] != login]
        result[n] = {"total": len(cs), "watermark": wm_id, "watermark_at": wm_at,
                     "unreviewed_count": len(newer),
                     "unreviewed": [{"id": c["id"], "user": c["user"]["login"],
                                     "at": c["created_at"], "len": len(c["body"]),
                                     "body": c["body"]} for c in newer]}
        u = result[n]
        print(f"#{n}: total={u['total']} watermark={wm_id}@{wm_at} unreviewed={u['unreviewed_count']}")
    (OUT / "coder_unreviewed_204.json").write_text(json.dumps(result, indent=1))
    # recently updated issues (catch new coder issues)
    rl = gh(f"https://api.github.com/repos/{REPO}/issues?state=all&sort=updated&direction=desc&per_page=30")
    print("\n-- 10 most recently updated issues --")
    for it in rl[:10]:
        kind = "PR" if "pull_request" in it else "issue"
        print(f"  #{it['number']} [{it['state']}] {kind} upd={it['updated_at']} by={it['user']['login']} :: {it['title'][:70]}")

if __name__ == "__main__":
    main()
