#!/usr/bin/env python3
"""S171 sweep: latest comments on #522/#525 + recent issues, to confirm nothing new after our S170 verdict posts."""
import json, subprocess

def token():
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUR_LAST = {6663595223, 6663595702}  # S170 verdict posts

def get(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}", url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception as e:
        return {"__error__": str(e), "raw": r.stdout[:200]}

for issue in (522, 525):
    cs = get(f"https://api.github.com/repos/{REPO}/issues/{issue}/comments?per_page=100&sort=created&direction=desc")
    if isinstance(cs, list):
        cs.sort(key=lambda c: (c["created_at"], c["id"]))
        print(f"=== #{issue}: {len(cs)} comments; last 3 ===")
        for c in cs[-3:]:
            first = (c["body"] or "").strip().split("\n")[0][:130]
            mark = " [OUR S170 POST]" if c["id"] in OUR_LAST else ""
            print(c["id"], c["created_at"], c["user"]["login"], "|", first + mark)
        newest = cs[-1] if cs else None
        if newest and newest["id"] not in OUR_LAST:
            print(f"  --> NEW SINCE OUR POST (id={newest['id']}, at={newest['created_at']}):")
            print(newest["body"][:3000])
    else:
        print(f"#{issue} fetch error:", cs)
    print()

il = get(f"https://api.github.com/repos/{REPO}/issues?state=all&sort=created&direction=desc&per_page=10")
if isinstance(il, list):
    print("=== 10 MOST RECENT ISSUES ===")
    for i in il:
        print(i["number"], i["created_at"], i["state"], "|", (i["title"] or "")[:100])
else:
    print("issue list error:", il)
