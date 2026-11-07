#!/usr/bin/env python3
"""S188-W11 re-verification battery: the impact-review fresh run.

Runs the SAME 11 titles as W10 on the byte-exact rebuilt binary
(73f4d87ac617ef4e) and compares tiers against W2 / W7 / W10 records.
Incremental save after EVERY app so an interrupted run loses nothing;
already-recorded apps are skipped on re-run.

Output: evidence/s188_w11/W11_REVERIFICATION.json
"""
import json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

OUT = BASE / 'evidence/s188_w11'
OUT.mkdir(parents=True, exist_ok=True)
w2.OUT = OUT
w2.RUNS = OUT / 'runs'
RES = OUT / 'W11_REVERIFICATION.json'

TITLES = [
    'com.justdeax.composeStopwatch', 'tibarj.tranquilstopwatch',
    'com.qwde.ccm', 'eu.quelltext.memory', 'cos.premy.mines',
    'eu.veldsoft.no.thanks', 'com.sidhant.queens',
    'com.simondalvai.ball2box', 'xyz.deepdaikon.quinb',
    'org.secuso.privacyfriendlybattleship',
    'crypto.o0o0o0o0o.games.blackjack',
]


def load_results():
    if RES.exists():
        d = json.loads(RES.read_text())
        if isinstance(d, dict):
            return d.get('results', [])
        return d
    return []


def save(results):
    RES.write_text(json.dumps(results, indent=1))


def main(only=None):
    results = load_results()
    done = {r['pkg'] for r in results if r.get('status') == 'OK'}
    for t in TITLES:
        if only and t not in only:
            continue
        if t in done:
            print('== skip (done)', t, flush=True)
            continue
        print('==', t, flush=True)
        apk = BASE / f'upload/stuck_apks/{t}.apk'
        if not apk.exists():
            results.append(dict(pkg=t, status='NO_APK'))
            save(results)
            continue
        try:
            results.append(w2.run_one(t, str(apk)))
        except Exception as e:
            results.append(dict(pkg=t, status='RUN_ERR', error=str(e)[:200]))
        save(results)

    # verdict table
    def tiers(path, ok_only=True):
        try:
            rows = json.load(open(path))
            return {e['pkg']: (e.get('tier'), e.get('uncaught_marks'))
                    for e in rows if (e.get('status') == 'OK' or not ok_only)}
        except Exception:
            return {}

    w2r = tiers(BASE / 'evidence/s188_w2/W2_FIRST_RENDERS.json')
    w7r = tiers(BASE / 'evidence/s188_w7/W7_BATTERY.json')
    w10r = tiers(BASE / 'evidence/s188_w10/W10_BATTERY.json')

    print(f"\n{'pkg':40s} {'W2':>22s} {'W10rec':>22s} {'W11fresh':>22s} {'u':>2s} verdict")
    drops = 0
    summary = []
    for r in results:
        if r.get('status') != 'OK':
            print(f"{r['pkg']:40s} RUN-FAIL {r.get('status')}")
            drops += 1
            summary.append(dict(pkg=r['pkg'], verdict='RUN_FAIL', status=r['status']))
            continue
        old10 = w10r.get(r['pkg'], ('-', None))[0]
        new = r.get('tier', '?')
        u = r.get('uncaught_marks', -1)
        u10 = w10r.get(r['pkg'], ('-', None))[1]
        if old10 != '-' and new != old10:
            if new != 'FLAT_TWO_TONE_OR_BLANK':
                verdict = 'ADVANCED'
            else:
                verdict = 'REGRESSED'
                drops += 1
        else:
            verdict = 'HOLD'
        print(f"{r['pkg']:40s} {w2r.get(r['pkg'],('-','-'))[0] or '-':>22s} {old10:>22s} {new:>22s} {u:>2d} {verdict}")
        summary.append(dict(pkg=r['pkg'], verdict=verdict, tier=new,
                            uncaught=u, uncaught_w10=u10))
    out = dict(wave='S188-W11 re-verification battery (impact review)',
               binary_sha16='73f4d87ac617ef4e',
               results=results, verdicts=summary, tier_drops=drops)
    save(out)
    print(f"\nTOTAL apps={len(results)} drops={drops}")
    return drops


if __name__ == '__main__':
    only = set(sys.argv[1:]) or None
    sys.exit(0 if main(only) == 0 else 1)
