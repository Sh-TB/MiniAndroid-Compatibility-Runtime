#!/usr/bin/env python3
# cont44_c_registry_grep.py — CONT44-C: grep root_registry.json rows per app keyword.
import json, re, sys

REG = '/home/z/my-project/root_registry.json'
r = json.load(open(REG))
roots = r['roots']
print(f"registry rows: {len(roots)}  generated: {r.get('generated')}")

KEYWORDS = [
    'tananaev', 'calculator', 'dooz', 'yamin8000', 'composeStopwatch', 'compose-stopwatch', 'csw',
    'opencalc', 'opencalculator', 'unote', 'varlorg', 'microtimer', 'microtimer', 'gmdice',
    'notes', 'secuso', 'sudoku', 'forkgram', 'telegram', 'whatsapp', 'klondike', 'bouncy',
    'opmt', 'fishrings', 'tripeaks', 'chess', 'jwtc', 'chessclock', 'stopwatch', 'muellerma',
    'tictactoe', 'emmanuelmess', 'flappy', '2048', 'snake', 'tetris', 'simplecalc',
    'preference', 'PreferenceFragment', 'F-NEW-304', 'F-NEW-305', 'F-NEW-306', 'F-NEW-307',
]

out = {}
for kw in KEYWORDS:
    pat = re.compile(re.escape(kw), re.IGNORECASE)
    hits = []
    for row in roots:
        blob = json.dumps(row, ensure_ascii=False)
        if pat.search(blob):
            hits.append({k: row.get(k) for k in ('id', 'status', 'priority', 'title', 'date')})
    out[kw] = hits
    if hits:
        print(f"\n== {kw} ({len(hits)} rows):")
        for h in hits[:12]:
            print(f"   {h['id']:14s} {h['status']:10s} P{h['priority']}  {str(h['title'])[:110]}")

json.dump(out, open('/home/z/my-project/run/cont44/registry_grep.json', 'w'), indent=1)
print("\nwrote run/cont44/registry_grep.json")
