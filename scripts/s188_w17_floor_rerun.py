#!/usr/bin/env python3
"""S188-W17: 11-title regression-floor rerun on the W17 binary
(a485e9826b618c35) — the F-NEW-601/602/603/604 edits touch broad dispatch
paths (interface resolution, bridge_to_api entry, native block, EGL
shadow body); the floor law requires the W12/W13 recorded tiers to hold.
Same run_one, same stage law, tier floors from the W13 battery.
"""
import json, sys, re, time
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w17/floor_rerun'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

FLOOR = {
    'com.justdeax.composeStopwatch': 'FLAT_TWO_TONE_OR_BLANK',
    'tibarj.tranquilstopwatch': 'FLAT_TWO_TONE_OR_BLANK',
    'com.qwde.ccm': 'FLAT_TWO_TONE_OR_BLANK',
    'eu.quelltext.memory': 'B_STRUCTURED',
    'cos.premy.mines': 'B_STRUCTURED',
    'eu.veldsoft.no.thanks': 'B_STRUCTURED',
    'com.sidhant.queens': 'FLAT_TWO_TONE_OR_BLANK',
    'com.simondalvai.ball2box': 'FLAT_TWO_TONE_OR_BLANK',
    'xyz.deepdaikon.quinb': 'FLAT_TWO_TONE_OR_BLANK',
    'org.secuso.privacyfriendlybattleship': 'FLAT_TWO_TONE_OR_BLANK',
    'crypto.o0o0o0o0o.games.blackjack': 'B_STRUCTURED',
}
ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'C_TEXT_ON_FLAT': 1,
         'B_STRUCTURED': 2, 'A_RICH': 3}

results = []
for t, floor in FLOOR.items():
    apk = BASE / f'upload/stuck_apks/{t}.apk'
    t0 = time.time()
    r = w2.run_one(t, str(apk))
    r['wall_s'] = round(time.time() - t0, 1)
    tier = r.get('tier') or (r.get('timed_face') or {}).get('tier')
    r['floor'] = floor
    r['regression'] = bool(tier in ORDER and floor in ORDER
                           and ORDER[tier] < ORDER[floor])
    r['face_sha'] = None
    results.append(r)
    print(f"{t:42s} tier={tier} floor={floor} "
          f"{'REGRESSION' if r['regression'] else 'HOLD'} wall={r['wall_s']}s",
          flush=True)
    with open(w2.OUT / 'floor_rerun.partial.json', 'w') as f:
        json.dump(results, f, indent=1)

drops = [r['pkg'] for r in results if r['regression']]
(w2.OUT / 'FLOOR_RERUN.json').write_text(json.dumps(
    {'binary': 'a485e9826b618c35', 'titles': len(results),
     'drops': drops, 'rows': results}, indent=1))
print('FLOOR', 'CLEAN 11/11' if not drops else f'REGRESSION x{len(drops)}')
