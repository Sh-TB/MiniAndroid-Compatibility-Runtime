#!/usr/bin/env python3
"""S177: fresh sweep of ALL coder trackers + our verdict issues for anything
newer than the S176 fetch (S176 ran ~2026-11-05T21:30Z+). Purpose: the master
directive's "achievement logs != integrated state" — catch deliveries that
landed after the S176 snapshot (C8 wave-7, C7 wave-4, C9 patch#3, C2/C3/C6
updates, replies to our verdicts)."""
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
OUT = "evidence/s177_sweep"
os.makedirs(OUT, exist_ok=True)

# S176 fetch cutoff: last known comment ids per issue (from s176 evidence)
KNOWN_LAST = {}

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}", url],
                       capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return None

ISSUES = {472: "Coder2", 492: "Coder3-tracker", 515: "Coder6", 518: "Coder4-W9",
          519: "Coder8", 520: "Coder7", 521: "Coder9", 522: "Coder4-W7",
          523: "Coder3-A15", 524: "Coder3-A16", 525: "Coder4-W10", 526: "Coder4-W10laws",
          527: "Coder3-A17"}

# load S176 baseline last-comment timestamps
base = json.load(open("evidence/s176_inventory/inventory_fetch_summary.json"))
for row in base:
    KNOWN_LAST[row["issue"]] = row["last_comment_at"]

# our own verdict comment ids (never count as new deliveries)
OURS = {6670079707, 6669725035, 6660079707, 6663595702, 6663595223}

summary = []
for iss, who in ISSUES.items():
    issue = api(f"https://api.github.com/repos/{REPO}/issues/{iss}")
    if not isinstance(issue, dict): print(f"#{iss} FETCH FAIL"); continue
    cs = []
    for p in range(1, 15):
        page = api(f"https://api.github.com/repos/{REPO}/issues/{iss}/comments?per_page=100&page={p}")
        if not isinstance(page, list) or not page: break
        cs += page
        if len(page) < 100: break
    cs.sort(key=lambda c: (c["created_at"], c["id"]))
    cutoff = KNOWN_LAST.get(iss)
    new = [c for c in cs if c["id"] not in OURS and
           (cutoff is None or c["created_at"] > cutoff)]
    # also treat replies to our verdicts (created after our post) as new
    body = issue.get("body") or ""
    row = {"issue": iss, "who": who, "title": (issue.get("title") or "")[:110],
           "state": issue.get("state"), "body_chars": len(body),
           "comments": len(cs), "last_comment_at": cs[-1]["created_at"] if cs else None,
           "new_since_s176": len(new), "new_ids": [c["id"] for c in new]}
    summary.append(row)
    flag = "  <<< NEW" if new else ""
    print(f"#{iss} [{who}] comments={len(cs)} last={row['last_comment_at']} new={len(new)}{flag}")
    for c in new:
        cb = c.get("body") or ""
        head = " ".join(cb.split())[:180]
        print(f"    + id={c['id']} {c['created_at']} {len(cb)}ch: {head}")
        with open(f"{OUT}/{iss}_comment_{c['id']}.md", "w") as f:
            f.write(f"# NEW comment on #{iss} [{who}] id={c['id']} {c['created_at']}\n\n{cb}")
    if new or len(body) != sum(1 for _ in open(f"/dev/null")):
        with open(f"{OUT}/{iss}_body_now.md", "w") as f:
            f.write(f"# ISSUE {iss} [{who}] state={issue.get('state')}\n\n{body}")

json.dump(summary, open(f"{OUT}/s177_sweep_summary.json", "w"), indent=1)
print("saved ->", OUT)
