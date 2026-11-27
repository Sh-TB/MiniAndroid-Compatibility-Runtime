#!/usr/bin/env python3
"""FINAL W32 analysis: fetch live P0 issue bodies + #599 comments + F-NEW-685 search retry.
Read-only. Token from git credential helper, never printed."""
import json, subprocess, time

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
    p = subprocess.run(["curl", "-sS", "-m", "30", "-H", f"Authorization: token {t}",
                        "-H", "Accept: application/vnd.github+json",
                        f"https://api.github.com{path}"], capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"_err": p.stdout[:300]}

out = {}
# The live P0 set
for n in (706, 705, 704, 703, 697, 699):
    iss = api(f"/repos/{REPO}/issues/{n}")
    out[f"i{n}"] = {"title": (iss.get("title") or "")[:130], "state": iss.get("state"),
                    "comments": iss.get("comments"),
                    "body_head": (iss.get("body") or "")[:2600]}
    time.sleep(1)
# F-NEW-685 search retry
sr = api(f"/search/issues?q=%22F-NEW-685%22+repo:{REPO}")
out["fnew685"] = {"total": sr.get("total_count"), "err": sr.get("message"),
                  "items": [{"n": i.get("number"), "t": (i.get("title") or "")[:100]}
                            for i in sr.get("items", [])[:6]]}
time.sleep(2)
# #599 recent comments (the final report target)
cm = api(f"/repos/{REPO}/issues/599/comments?per_page=6&sort=created&direction=desc")
out["i599_comments"] = [{"id": c.get("id"), "at": c.get("created_at"),
                         "head": (c.get("body") or "")[:350]}
                        for c in cm if isinstance(c, dict)]
json.dump(out, open("/home/z/my-project/scripts/w32_issue_analysis.json", "w"), indent=1)
for n in (706, 705, 704, 703, 697, 699):
    d = out[f"i{n}"]
    print(f"=== #{n} [{d['state']}] {d['title']}")
    print(d["body_head"][:1800].replace("\r", ""))
    print()
print("FNEW685:", json.dumps(out["fnew685"])[:600])
print("#599 comments:")
for c in out["i599_comments"]:
    print(f"  id={c['id']} {c['at']}: {c['head'][:200]}")
