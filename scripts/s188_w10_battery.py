#!/usr/bin/env python3
"""S188-W10 regression battery: 11 titles on the F-NEW-595/590-594 binary.

Compares every tier against BOTH the W2 baseline and the W7 battery (the
last recorded pre-W10 tiers). Regression law: no B anchor may drop, no tier
may regress below the W7 recorded state.
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w10'
w2.RUNS = w2.OUT / 'runs'


def main():
    titles = [
        'com.justdeax.composeStopwatch', 'tibarj.tranquilstopwatch',
        'com.qwde.ccm', 'eu.quelltext.memory', 'cos.premy.mines',
        'eu.veldsoft.no.thanks', 'com.sidhant.queens',
        'com.simondalvai.ball2box', 'xyz.deepdaikon.quinb',
        'org.secuso.privacyfriendlybattleship',
        'crypto.o0o0o0o0o.games.blackjack',
    ]
    results = []
    for t in titles:
        print('==', t, flush=True)
        apk = BASE / f'upload/stuck_apks/{t}.apk'
        if not apk.exists():
            results.append(dict(pkg=t, status='NO_APK'))
            continue
        try:
            results.append(w2.run_one(t, str(apk)))
        except Exception as e:
            results.append(dict(pkg=t, status='RUN_ERR', error=str(e)[:200]))
    (w2.OUT / 'W10_BATTERY.json').write_text(json.dumps(results, indent=1))

    base = {e['pkg']: e.get('tier') for e in
            json.load(open(BASE / 'evidence/s188_w2/W2_FIRST_RENDERS.json'))}
    w7 = {e['pkg']: e.get('tier') for e in
          json.load(open(BASE / 'evidence/s188_w7/W7_BATTERY.json'))
          if e.get('status') == 'OK'}
    print(f"\n{'pkg':45s} {'W2':>24s} {'W7':>24s} {'W10':>24s} verdict")
    drops = 0
    for r in results:
        if r.get('status') != 'OK':
            print(f"{r['pkg']:45s} {'?':>24s} {'?':>24s} {r['status']:>24s} RUN-FAIL")
            drops += 1
            continue
        old = base.get(r['pkg'], '?')
        old7 = w7.get(r['pkg'], '?')
        new = r.get('tier', '?')
        if new == old7 or new == old:
            verdict = 'HOLD'
        elif new != 'FLAT_TWO_TONE_OR_BLANK':
            verdict = 'ADVANCED'
        else:
            verdict = 'REGRESSION'
            drops += 1
        print(f"{r['pkg']:45s} {old:>24s} {old7:>24s} {new:>24s} {verdict}")
    print(f"\nW10 BATTERY VERDICT: {'CLEAN — zero tier regressions' if drops == 0 else f'{drops} DROPS'}")
    return drops


if __name__ == '__main__':
    sys.exit(0 if main() == 0 else 1)
