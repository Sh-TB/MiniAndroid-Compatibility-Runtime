#!/usr/bin/env python3
"""S175: fetch chain issues #508/#511/#513/#516/#523/#524 (A11..A16) — look for the A17 code delta (patch text)."""
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

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}", url],
                       capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception as e: print("PARSE-ERR", url, e); return None

for iss in (508, 511, 513, 516, 523, 524):
    issue = api(f"https://api.github.com/repos/{REPO}/issues/{iss}")
    if not issue: continue
    body = issue.get("body") or ""
    title = issue.get("title", "")
    with open(f"{OUT}/{iss}_body.md", "w") as f:
        f.write(f"# ISSUE {iss}: {title}\n\n{body}")
    has_patch = ("diff --git" in body) or ("patch" in body.lower()[:2000])
    print(f"#{iss} [{issue.get('state')}] {title[:100]} | body {len(body)}ch | patch-inline={has_patch}")
    # first comment presence
    cs = api(f"https://api.github.com/repos/{REPO}/issues/{iss}/comments?per_page=100")
    if isinstance(cs, list) and cs:
        print(f"   comments: {len(cs)}; last id {cs[-1]['id']} {cs[-1]['created_at']}")
        for c in cs:
            cb = c.get("body") or ""
            if "diff --git" in cb:
                print(f"   COMMENT {c['id']} CONTAINS PATCH TEXT ({len(cb)} ch)")
