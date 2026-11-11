#!/usr/bin/env python3
"""S216 sweep pass 2 — full-comment fetch WITH edit detection against the
stored 08:54Z sweep + a FULL snapshot baseline for future edit detection.
 (a) NEW comments  (id > watermark 6788287658)
 (b) EDITED comments (updated_at / len changed vs any prior observation)
Writes: evidence/s216/s216_sweep2.json + evidence/s216/s216_full_snapshot.json
"""
import json, os, subprocess, time
from urllib.request import Request, urlopen

TOKEN = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n", capture_output=True, text=True
).stdout.split("password=")[-1].strip()

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
WATERMARK = 6788287658
HOT_ISSUES = [581, 577, 519, 570, 573, 536, 520, 9, 575, 557, 492, 521, 580]
PRIOR = "evidence/s216/s216_sweep.json"
OUT = "evidence/s216/s216_sweep2.json"
SNAP = "evidence/s216/s216_full_snapshot.json"


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


prior = {}
if os.path.exists(PRIOR):
    for iss, rec in json.load(open(PRIOR)).get("issues", {}).items():
        for c in rec.get("new", []):
            prior[f"{iss}:{c['id']}"] = {"updated": c["updated"], "len": c["len"]}

snapshot = {}
sweep = {"watermark": WATERMARK,
         "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "issues": {}}
new_total, edited_total = 0, 0
for issue in HOT_ISSUES:
    cs = all_comments(issue)
    recs, cur = [], {}
    for c in cs:
        cur[c["id"]] = {"updated": c["updated_at"], "len": len(c["body"])}
        recs.append({"id": c["id"], "author": c["user"]["login"],
                     "created": c["created_at"], "updated": c["updated_at"],
                     "len": len(c["body"]),
                     "head": c["body"][:180].replace("\n", " ")})
    snapshot[str(issue)] = cur
    new = [r for r in recs if r["id"] > WATERMARK]
    edited = []
    for r in recs:
        key = f"{issue}:{r['id']}"
        if key in prior and (prior[key]["updated"] != r["updated"]
                             or prior[key]["len"] != r["len"]):
            edited.append({"id": r["id"], "was_updated": prior[key]["updated"],
                           "now_updated": r["updated"],
                           "was_len": prior[key]["len"], "now_len": r["len"]})
    sweep["issues"][str(issue)] = {
        "n_comments": len(recs), "new": new, "edited": edited}
    new_total += len(new)
    edited_total += len(edited)
    print(f"#{issue}: {len(recs)} comments, NEW={len(new)}, EDITED={len(edited)}",
          flush=True)
    for r in new:
        print(f"   NEW {r['id']} {r['author']} {r['created']} len={r['len']}: "
              f"{r['head'][:110]}")
    for e in edited:
        print(f"   EDIT {e['id']} {e['was_updated']} -> {e['now_updated']} "
              f"len {e['was_len']}->{e['now_len']}")

sweep["new_total"], sweep["edited_total"] = new_total, edited_total
json.dump(sweep, open(OUT, "w"), indent=1)
json.dump(snapshot, open(SNAP, "w"))
print(f"TOTAL: new={new_total} edited={edited_total} -> {OUT}")
print(f"FULL SNAPSHOT (id -> updated/len) -> {SNAP}")
