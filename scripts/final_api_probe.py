#!/usr/bin/env python3
"""S-SLIM/FINAL: read-only GitHub API probes for issue #599 + F-NEW-685 record.
Token comes from the git credential helper; it is never printed or stored."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def token():
    inp = "protocol=https\nhost=github.com\n\n"
    out = subprocess.run(["git", "credential", "fill"], input=inp, capture_output=True,
                         text=True, cwd="/home/z/my-project")
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    return None

def api(path):
    t = token()
    cmd = ["curl", "-sS", "-m", "30", "-H", f"Authorization: token {t}",
           "-H", "Accept: application/vnd.github+json",
           f"https://api.github.com{path}"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"_raw": p.stdout[:500], "_err": p.stderr[:300]}

res = {}
# 1. Issue #599
iss = api(f"/repos/{REPO}/issues/599")
res["issue599"] = {k: iss.get(k) for k in ("number", "title", "state", "comments", "created_at", "updated_at")}
body = iss.get("body") or ""
res["issue599_body_head"] = body[:1500]
res["issue599_body_len"] = len(body)
# 2. F-NEW-685 search
sr = api(f"/search/issues?q=F-NEW-685+repo:{REPO}")
res["fnew685_total"] = sr.get("total_count")
res["fnew685_items"] = [{"n": i.get("number"), "t": i.get("title"), "state": i.get("state")}
                        for i in sr.get("items", [])[:5]]
# 3. removeView family search
sr2 = api(f"/search/issues?q=removeView+repo:{REPO}")
res["removeview_total"] = sr2.get("total_count")
res["removeview_items"] = [{"n": i.get("number"), "t": i.get("title"), "state": i.get("state")}
                           for i in sr2.get("items", [])[:8]]
# 4. Open issues count / latest few for campaign state
sr3 = api(f"/repos/{REPO}/issues?state=open&sort=updated&direction=desc&per_page=12")
res["open_recent"] = [{"n": i.get("number"), "t": (i.get("title") or "")[:70], "upd": i.get("updated_at")}
                      for i in sr3 if isinstance(i, dict) and "pull_request" not in i]

json.dump(res, open("/home/z/my-project/scripts/api599_result.json", "w"), indent=1)
# printed summary (no token anywhere)
print("ISSUE599:", json.dumps(res["issue599"], indent=1)[:400])
print("BODY_HEAD:", res["issue599_body_head"][:900])
print("FNEW685_total:", res["fnew685_total"], res["fnew685_items"])
print("REMOVEVIEW_total:", res["removeview_total"])
for it in res["removeview_items"]:
    print("  ", it)
print("OPEN_RECENT:")
for it in res["open_recent"]:
    print("  ", it)
