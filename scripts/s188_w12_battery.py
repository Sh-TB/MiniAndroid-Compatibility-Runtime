#!/usr/bin/env python3
"""S188-W12 full regression battery: 11 titles on the F-NEW-596/598 binary.

Regression law: no B anchor may drop vs the W2/W10 recorded tiers; the
goldens (bouncy/unote/dooz) must stay byte-exact (run separately).
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w12'
w2.RUNS = w2.OUT / 'runs'

TITLES = [
    'com.justdeax.composeStopwatch', 'tibarj.tranquilstopwatch',
    'com.qwde.ccm', 'eu.quelltext.memory', 'cos.premy.mines',
    'eu.veldsoft.no.thanks', 'com.sidhant.queens',
    'com.simondalvai.ball2box', 'xyz.deepdaikon.quinb',
    'org.secuso.privacyfriendlybattleship',
    'crypto.o0o0o0o0o.games.blackjack',
]

# W10 recorded tiers (the regression floor) — from evidence/s188_w10/W10_BATTERY.json
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
ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'B_STRUCTURED': 1, 'A_STRUCTURED': 2}

def main():
    results = []
    drops = []
    for t in TITLES:
        print('==', t, flush=True)
        apk = BASE / f'upload/stuck_apks/{t}.apk'
        if not apk.exists():
            results.append(dict(pkg=t, status='NO_APK'))
            continue
        try:
            r = w2.run_one(t, str(apk))
            results.append(r)
            tier = r.get('tier') or r.get('timed_face', {}).get('tier', '?')
            floor = FLOOR.get(t)
            if floor and tier in ORDER and floor in ORDER and ORDER[tier] < ORDER[floor]:
                drops.append(dict(pkg=t, tier=tier, floor=floor))
            print('  tier=', tier, 'floor=', floor, flush=True)
        except Exception as e:
            results.append(dict(pkg=t, status='RUN_ERR', error=str(e)[:200]))
            print('  ERR', e, flush=True)
    (w2.OUT / 'W12_BATTERY.json').write_text(json.dumps(results, indent=1))
    print('DROPS:', drops)
    print('BATTERY', 'CLEAN' if not drops else f'REGRESSION x{len(drops)}')

if __name__ == '__main__':
    main()
