#!/usr/bin/env python3
"""S195 AUDIT — fetch ALL comments for the priority issue set (MAIN CODER
MASTER TASK §1). Incremental partial JSON (partial-loss law)."""
import json, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s195_audit'
OUT.mkdir(parents=True, exist_ok=True)

PRIORITY = (
    # Coder 2 / Coder 5
    [450, 472, 505] + list(range(446, 469)) + [475, 480, 484, 490]
    # Coder 3
    + [492, 557, 561, 560, 540, 537, 535, 530, 516, 513, 511]
    # Coder 4
    + list(range(430, 437)) + [510, 512, 514, 517, 518, 522, 525, 526, 528,
                               534, 538, 558, 562, 563, 564, 566]
    # Coder 6
    + [437, 438, 439, 440, 441, 515]
    # Coder 7 / Coder 8 / Coder 9
    + [520, 519, 533, 521]
    # S188 governance + integration
    + [536, 541, 542] + list(range(543, 560)) + [565, 556]
)
PRIORITY = sorted(set(PRIORITY))


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
PART = OUT / 'comments_raw.partial.json'
done = {}
if PART.exists():
    try:
        done = json.loads(PART.read_text())
        print(f"resuming: {len(done)} issues already fetched")
    except Exception:
        done = {}

for n in PRIORITY:
    if str(n) in done:
        continue
    cs, page = [], 1
    while True:
        r = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: token {TOK}",
             f"https://api.github.com/repos/{REPO}/issues/{n}/comments"
             f"?per_page=100&page={page}"],
            capture_output=True, text=True)
        try:
            batch = json.loads(r.stdout)
        except Exception as e:
            print(f"#{n} page {page} parse error: {e}")
            batch = []
        if not isinstance(batch, list) or not batch:
            break
        cs += batch
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.3)
    done[str(n)] = [{'id': c['id'], 'created_at': c['created_at'],
                     'updated_at': c['updated_at'],
                     'user': c['user']['login'] if c.get('user') else None,
                     'body': c['body']} for c in cs]
    print(f"#{n}: {len(cs)} comments", flush=True)
    PART.write_text(json.dumps(done))
    time.sleep(0.25)

(OUT / 'comments_raw.json').write_text(json.dumps(done))
total = sum(len(v) for v in done.values())
print(f"DONE: {len(done)} issues, {total} comments total")
