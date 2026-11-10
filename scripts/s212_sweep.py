#!/usr/bin/env python3
"""S212 — repo-wide comments since the S211 watermark (2026-11-10T17:37Z).
Uses the repo-level issues/comments endpoint with since= (1-2 API calls instead
of paginating 462 issues). Output: evidence/s212/s212_sweep.json."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
SINCE = "2026-11-10T17:00:00Z"   # just before my S211 verdict comments
OUT = Path('/home/z/my-project/evidence/s212')
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
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_curl_error": r.stdout[:200], "_status": r.returncode}

def main():
    all_new, page = [], 1
    while True:
        batch = gh(f"https://api.github.com/repos/{REPO}/issues/comments"
                   f"?per_page=100&page={page}&sort=created&direction=desc"
                   f"&since={SINCE}")
        if not isinstance(batch, list) or not batch:
            break
        all_new.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 5:
            break
    mine = [c for c in all_new if c["user"]["login"] == "Sh-TB"]
    theirs = [c for c in all_new if c["user"]["login"] != "Sh-TB"]
    result = {"since": SINCE, "fetched": len(all_new),
              "mine_count": len(mine),
              "mine_ids": [c["id"] for c in sorted(mine, key=lambda c: c["id"])],
              "theirs_count": len(theirs),
              "theirs": [{"issue": int(c["issue_url"].rsplit("/", 1)[1]),
                          "id": c["id"], "user": c["user"]["login"],
                          "at": c["created_at"], "len": len(c["body"]),
                          "body": c["body"]} for c in theirs]}
    (OUT / "s212_sweep.json").write_text(json.dumps(result, indent=1))
    print(f"fetched={len(all_new)} mine={len(mine)} theirs={len(theirs)}")
    print("MY watermark comments since S211:",
          sorted([c["id"] for c in mine]))
    for c in sorted(result["theirs"], key=lambda x: (x["issue"], x["id"])):
        print(f"NEW #{c['issue']} c={c['id']} by={c['user']} at={c['at']} len={c['len']}")
        print(f"     head: {c['body'][:150].replace(chr(10),' | ')}")

if __name__ == "__main__":
    main()
