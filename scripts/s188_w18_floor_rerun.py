#!/usr/bin/env python3
"""S188-W18: 11-title regression-floor rerun on the W18 binary — the W18
edits touch broad dispatch paths (the F-NEW-606 element-type family in
the snapshot/commit hooks, the F-NEW-607 descriptor-exact native
selection, the F-NEW-608 toCharArray/Character bridges, the F-NEW-609
persistent direct-buffer backing, the F-NEW-611 JNI mangling, the
F-NEW-613 shadow-claim gate); the floor law requires the W12/W13
recorded tiers to hold.
Same run_one, same stage law, tier floors from the W13 battery.
FIX (finalize): the binary sha is now computed from the on-disk binary
(dynamically) — the first run hardcoded a stale draft label (cc616a35)
while the battery recorded the true final binary 1f05270d793a43b5;
re-run for a correctly-labeled record.
"""
import json, sys, re, time, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w18/floor_rerun'
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
BIN_SHA = hashlib.sha256((BASE / 'miniandroid/build/miniandroid')
                         .read_bytes()).hexdigest()[:16]
(w2.OUT / 'FLOOR_RERUN.json').write_text(json.dumps(
    {'binary': BIN_SHA, 'titles': len(results),
     'drops': drops, 'rows': results}, indent=1))
print('FLOOR', 'CLEAN 11/11' if not drops else f'REGRESSION x{len(drops)}',
      'binary', BIN_SHA)
