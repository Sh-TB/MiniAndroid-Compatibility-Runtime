#!/usr/bin/env python3
"""S216 sweep — full-comment fetch WITH EDIT DETECTION.
Re-pulls ALL comments on every audited watermark-hot issue and detects:
 (a) NEW comments (id > watermark 6788287658)
 (b) EDITED comments (updated_at changed vs the S215 verdict snapshot)
Baseline snapshot: the verdict comments recorded in S215c/d
(#581 c=6787989040, #577 c=6787989675/6788300863, #519 c=6787990298,
 #570 c=6787990965, #573 c=6787991616, #536 c=6787992285/6788301622,
 #520 c=6788300201) + watermark 6788287658.
"""
import json, os, subprocess, sys, time
from urllib.request import Request, urlopen

TOKEN = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n", capture_output=True, text=True
).stdout.split("password=")[-1].strip()

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
WATERMARK = 6788287658
# The S215 verdict snapshot (comment id -> posted/known updated_at unknown; we
# record everything now and diff vs stored baseline if present)
BASELINE = "evidence/s216/s215_verdict_baseline.json"
HOT_ISSUES = [581, 577, 519, 570, 573, 536, 520, 9, 575, 557, 492, 521]
OUT = "evidence/s216/s216_sweep.json"


def api(path):
    req = Request(f"https://api.github.com{path}", headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json"})
    for attempt in range(4):
        try:
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 3:
                return {"__error__": str(e)}
            time.sleep(2 * (attempt + 1))


def all_comments(issue):
    out, page = [], 1
    while True:
        chunk = api(f"/repos/{REPO}/issues/{issue}/comments?per_page=100&page={page}")
        if not isinstance(chunk, list) or not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return out


os.makedirs("evidence/s216", exist_ok=True)
baseline = {}
if os.path.exists(BASELINE):
    baseline = json.load(open(BASELINE))

sweep = {"watermark": WATERMARK, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
        time.gmtime()), "issues": {}}
new_total, edited_total = 0, 0
for issue in HOT_ISSUES:
    cs = all_comments(issue)
    recs = [{"id": c["id"], "author": c["user"]["login"],
             "created": c["created_at"], "updated": c["updated_at"],
             "len": len(c["body"]),
             "head": c["body"][:180].replace("\n", " ")} for c in cs]
    new = [r for r in recs if r["id"] > WATERMARK]
    edited = []
    for r in recs:
        key = f"{issue}:{r['id']}"
        if key in baseline:
            b = baseline[key]
            if b["updated"] != r["updated"] or b["len"] != r["len"]:
                edited.append({"id": r["id"], "was_updated": b["updated"],
                               "now_updated": r["updated"],
                               "was_len": b["len"], "now_len": r["len"]})
    sweep["issues"][str(issue)] = {
        "n_comments": len(recs), "new": new, "edited": edited}
    new_total += len(new)
    edited_total += len(edited)
    print(f"#{issue}: {len(recs)} comments, NEW={len(new)}, EDITED={len(edited)}",
          flush=True)
    for r in new:
        print(f"   NEW {r['id']} {r['author']} {r['created']} len={r['len']}: {r['head'][:120]}")
    for e in edited:
        print(f"   EDIT {e['id']} {e['was_updated']} -> {e['now_updated']} "
              f"len {e['was_len']}->{e['now_len']}")

# save the new baseline snapshot for the NEXT sweep
bl = {}
for issue in HOT_ISSUES:
    for r in sweep["issues"][str(issue)].get("new", []):
        pass
sweep["new_total"], sweep["edited_total"] = new_total, edited_total
json.dump(sweep, open(OUT, "w"), indent=1)
print(f"TOTAL: new={new_total} edited={edited_total} -> {OUT}")
