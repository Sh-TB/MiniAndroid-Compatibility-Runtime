#!/usr/bin/env python3
"""S176: live integration inventory — fetch every coder tracker the master
directive names: #472 (C2), #492+#523+#524 (C3), #522/#525/#526/#527 (C4/C3),
#515 (C6), #520 (C7), #519 (C8), #521 (C9). Bodies + comment census."""
import json, subprocess, os

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "evidence/s176_inventory"
os.makedirs(OUT, exist_ok=True)

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}", url],
                       capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return None

ISSUES = {472: "Coder2", 492: "Coder3-tracker", 515: "Coder6", 519: "Coder8",
          520: "Coder7", 521: "Coder9", 523: "Coder3-A15", 524: "Coder3-A16"}

summary = []
for iss, who in ISSUES.items():
    issue = api(f"https://api.github.com/repos/{REPO}/issues/{iss}")
    if not issue: print(f"#{iss} FETCH FAIL"); continue
    body = issue.get("body") or ""
    with open(f"{OUT}/{iss}_body.md", "w") as f:
        f.write(f"# ISSUE {iss} [{who}]: {issue.get('title','')}\nstate={issue.get('state')} created={issue.get('created_at')}\n\n{body}")
    cs = []
    for p in range(1, 12):
        page = api(f"https://api.github.com/repos/{REPO}/issues/{iss}/comments?per_page=100&page={p}")
        if not isinstance(page, list) or not page: break
        cs += page
        if len(page) < 100: break
    cs.sort(key=lambda c: (c["created_at"], c["id"]))
    with open(f"{OUT}/{iss}_comments.json", "w") as f:
        json.dump(cs, f, indent=1)
    has_diff = ("diff --git" in body) or any("diff --git" in (c.get("body") or "") for c in cs)
    row = {"issue": iss, "who": who, "title": issue.get("title","")[:110],
           "state": issue.get("state"), "body_chars": len(body),
           "comments": len(cs), "last_comment_at": cs[-1]["created_at"] if cs else None,
           "patch_inline": has_diff}
    summary.append(row)
    print(f"#{iss} [{who}] {row['title'][:80]}")
    print(f"     body={len(body)}ch comments={len(cs)} last={row['last_comment_at']} patch_inline={has_diff}")

json.dump(summary, open(f"{OUT}/inventory_fetch_summary.json", "w"), indent=1)
print("saved ->", OUT)
