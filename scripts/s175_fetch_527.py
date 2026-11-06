#!/usr/bin/env python3
"""S175: fetch issue #527 (Coder-3 A17 dooz Material You delivery) full body + all comments,
and sweep #518/#522/#525/#526 for anything newer than our S174 verdict post (6670079707)."""
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
OUT = "evidence/s175_a17"
os.makedirs(OUT, exist_ok=True)
KNOWN = {6670079707, 6669725035, 6660079707, 6663595702, 6663595223}  # our verdict posts

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}", url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception as e:
        print("PARSE-ERR", url, e, r.stdout[:200]); return None

# --- Issue #527 body ---
issue = api(f"https://api.github.com/repos/{REPO}/issues/527")
if issue:
    with open(f"{OUT}/527_body.md", "w") as f:
        f.write(f"# ISSUE 527: {issue.get('title','')}\nstate={issue.get('state')} created={issue.get('created_at')} by {issue.get('user',{}).get('login')}\n\n{issue.get('body','')}")
    print("=== #527:", issue.get("title",""))
    print("body chars:", len(issue.get("body") or ""))

# --- Comments on all watched issues ---
for iss in (527, 526, 518, 522, 525):
    all_c = []
    for p in range(1, 12):
        cs = api(f"https://api.github.com/repos/{REPO}/issues/{iss}/comments?per_page=100&page={p}")
        if not isinstance(cs, list) or not cs: break
        all_c += cs
        if len(cs) < 100: break
    all_c.sort(key=lambda c: (c["created_at"], c["id"]))
    new = [c for c in all_c if c["id"] not in KNOWN]
    print(f"--- #{iss}: total {len(all_c)} comments; NEW (unprocessed): {len(new)}")
    for c in all_c[-6:]:
        first = (c["body"] or "").strip().split("\n")[0][:120]
        mark = " [OURS/KNOWN]" if c["id"] in KNOWN else " [NEW]"
        print("   ", c["id"], c["created_at"], c["user"]["login"], "|", first + mark)
    if iss == 527 and all_c:
        with open(f"{OUT}/527_comments.json", "w") as f:
            json.dump(all_c, f, indent=1)
        for c in all_c:
            with open(f"{OUT}/527_comment_{c['id']}.md", "w") as f:
                f.write(c["body"] or "")
    elif new:
        with open(f"{OUT}/sweep_{iss}_new.json", "w") as f:
            json.dump(new, f, indent=1)
