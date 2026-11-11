#!/usr/bin/env python3
"""S215 sweep: repo-wide comment scan catching BOTH new comments AND edits.

User instruction: coders don't just post new comments, they also EDIT existing
comments. So instead of only id > watermark, we sort the repo-wide comment feed
by updated_at desc and flag:
  - NEW:      comment id > watermark (6787176796)
  - EDITED:   comment id <= watermark but updated_at > ref_time
              (ref_time = created_at of the watermark verdict comment)
Also: issue list with their updated_at (new issues / edited issue bodies).
Auth: git credential fill.
"""
import json
import subprocess
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
WATERMARK_ID = 6787176796
WATERMARK_REF_COMMENT = 6787176796  # SF-order verdict on #376

cred = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project"
).stdout
token = ""
for line in cred.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    print("NO TOKEN", file=sys.stderr)
    sys.exit(1)


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s215-sweep",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def paged(url):
    out, page = [], 1
    while True:
        sep = "&" if "?" in url else "?"
        batch = api(f"{url}{sep}per_page=100&page={page}")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


# 1. ref time = created_at of watermark comment
wm = api(f"https://api.github.com/repos/{REPO}/issues/comments/{WATERMARK_REF_COMMENT}")
ref_time = wm["created_at"]
print(f"REF_TIME (watermark comment created_at) = {ref_time}")
print(f"watermark comment on issue #{wm['issue_url'].rsplit('/', 1)[-1]}")

# 2. repo-wide comments sorted by updated desc
comments = paged(f"https://api.github.com/repos/{REPO}/issues/comments"
                 "?sort=updated&direction=desc")
print(f"total comments in feed: {len(comments)}")

news, edits = [], []
for c in comments:
    if c["id"] > WATERMARK_ID:
        news.append(c)
    elif c["updated_at"] > ref_time:
        edits.append(c)

news.sort(key=lambda c: c["id"])
edits.sort(key=lambda c: c["updated_at"])

print(f"\n=== NEW since watermark ({len(news)}) ===")
for c in news:
    issue = c["issue_url"].rsplit("/", 1)[-1]
    body = (c.get("body") or "").replace("\n", " ")
    print(f"c={c['id']} issue=#{issue} created={c['created_at']} "
          f"len={len(c.get('body') or '')} :: {body[:150]}")

print(f"\n=== EDITED after ref_time ({len(edits)}) ===")
for c in edits:
    issue = c["issue_url"].rsplit("/", 1)[-1]
    body = (c.get("body") or "").replace("\n", " ")
    print(f"c={c['id']} issue=#{issue} created={c['created_at']} "
          f"updated={c['updated_at']} len={len(c.get('body') or '')} :: {body[:150]}")

# 3. issue list (open, sorted by updated) — catch new issues + edited bodies
issues = paged(f"https://api.github.com/repos/{REPO}/issues?state=open&sort=updated&direction=desc")
print(f"\n=== OPEN ISSUES sorted by updated ({len(issues)}) ===")
for i in issues[:25]:
    is_pr = "pull_request" in i
    print(f"#{i['number']} up={i['updated_at']} cr={i['created_at']} "
          f"comments={i['comments']} pr={is_pr} :: {i['title'][:90]}")

# save full data for offline audit
with open("/tmp/s215_comments.json", "w") as f:
    json.dump({"ref_time": ref_time, "news": [
        {"id": c["id"], "issue": int(c["issue_url"].rsplit("/", 1)[-1]),
         "created": c["created_at"], "updated": c["updated_at"],
         "body": c.get("body") or ""} for c in news], "edits": [
        {"id": c["id"], "issue": int(c["issue_url"].rsplit("/", 1)[-1]),
         "created": c["created_at"], "updated": c["updated_at"],
         "body": c.get("body") or ""} for c in edits]}, f)
print("\nsaved /tmp/s215_comments.json")
