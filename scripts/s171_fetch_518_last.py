#!/usr/bin/env python3
"""S171: fetch last comments on issue #518 (coder delivery thread), list everything after the last processed IDs."""
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
ISSUE = 518
# Last processed on #518 (worklog S168/S170): 6638731163 = W7 delivery; 6653285018 = our S168 verification post.
KNOWN = {6638731163, 6653285018}

all_c = []
for p in range(1, 12):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}",
                        f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments?per_page=100&page={p}"],
                       capture_output=True, text=True)
    try:
        cs = json.loads(r.stdout)
    except Exception as e:
        print(f"page {p} parse error: {e}"); break
    if not isinstance(cs, list) or not cs:
        break
    all_c += cs
    if len(cs) < 100:
        break

all_c.sort(key=lambda c: (c["created_at"], c["id"]))
print("TOTAL COMMENTS ON #518:", len(all_c))
print("=== ALL (id | created_at | author | first line) ===")
for c in all_c:
    body = (c["body"] or "").strip().split("\n")[0][:140]
    mark = " [KNOWN]" if c["id"] in KNOWN else ""
    print(c["id"], c["created_at"], c["user"]["login"], "|", body + mark)

new = [c for c in all_c if c["id"] not in KNOWN]
new_after_known = [c for c in all_c if c["created_at"] > "2026-11-05"]
print("\n=== COMMENTS NOT YET PROCESSED (after 2026-11-05) ===")
for c in new_after_known:
    print("---")
    print(f"id={c['id']} at={c['created_at']} by={c['user']['login']} url={c['html_url']}")
    print(c["body"])

with open("/tmp/c518_all_sorted.json", "w") as f:
    json.dump(all_c, f)
print("\nsaved /tmp/c518_all_sorted.json")
