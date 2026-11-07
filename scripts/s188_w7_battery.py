#!/usr/bin/env python3
"""S188 W7: 11-title regression battery on the F-NEW-582/583 binary.

Reuses the W2 first-renders harness with evidence redirected to
evidence/s188_w7; compares every tier against the W2 baseline
(W2_FIRST_RENDERS.json). Regression law: no B anchor may drop.
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

# Redirect evidence paths to the W7 dir
w2.OUT = BASE / 'evidence/s188_w7'
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
            # fall back to the W2 manifest path
            man = json.load(open(BASE / 'evidence/s186_s107/S186C_STUCK_APK_MANIFEST.json'))
            rows = man if isinstance(man, list) else man.get('results', [])
            apk = next((r['path'] for r in rows
                        if r.get('pkg') == t and r.get('path')
                        and Path(r['path']).exists()), None)
            if not apk:
                results.append(dict(pkg=t, status='NO_APK')); continue
        try:
            results.append(w2.run_one(t, str(apk)))
        except Exception as e:
            results.append(dict(pkg=t, status='RUN_ERR', error=str(e)[:200]))
    (w2.OUT / 'W7_BATTERY.json').write_text(json.dumps(results, indent=1))

    # Compare against the W2 baseline
    base = {e['pkg']: e.get('tier') for e in
            json.load(open(BASE / 'evidence/s188_w2/W2_FIRST_RENDERS.json'))}
    print(f"\n{'pkg':45s} {'W2':>24s} {'W7':>24s} verdict")
    drops = 0
    for r in results:
        if r.get('status') != 'OK':
            print(f"{r['pkg']:45s} {'?':>24s} {r['status']:>24s} RUN-FAIL")
            drops += 1
            continue
        old = base.get(r['pkg'], '?')
        new = r.get('tier', '?')
        verdict = 'HOLD' if new == old else ('ADVANCED' if new != old and old == 'FLAT_TWO_TONE_OR_BLANK' else 'REGRESSION')
        if verdict == 'REGRESSION':
            drops += 1
        print(f"{r['pkg']:45s} {old:>24s} {new:>24s} {verdict}")
    print('VERDICT:', 'BATTERY CLEAN' if drops == 0 else f'{drops} ISSUES')


if __name__ == '__main__':
    main()
