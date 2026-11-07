#!/usr/bin/env python3
"""S188-W13: >=20-title LOADING-PROGRESS battery (user directive:
"test at least 20 apps and games, see whether they made progress in
loading"). 24 titles = 11 regression-floor titles (W12 recorded tiers)
+ 13 fresh titles from the stuck_apks corpus.

Per title we record the honest LOADING-CHAIN STAGE reached:
  S0 INSTALL_FAIL
  S1 RUN_LAUNCHED
  S2 ROUTE_DECIDED      ([ROUTE] DECISION printed at boot)
  S3 ACTIVITY_LIFECYCLE (activity entered without fatal)
  S4 SUBSYSTEM_LOADED   (dlopen libflutter/libgodot/webview/compose/GLES)
  S5 RENDER_PRODUCED    (a screenshot frame exists)
  S6 SETTLED_FACE_TIERED(frames time-driven cross-check completed)

Incremental persistence: every finished title is appended to
W13_BATTERY.partial.json so a sandbox recycle never loses runs.
"""
import json, sys, re, time, traceback
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w13'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

# 11 titles with a recorded W12 tier floor (regression law)
KNOWN = [
    'com.justdeax.composeStopwatch', 'tibarj.tranquilstopwatch',
    'com.qwde.ccm', 'eu.quelltext.memory', 'cos.premy.mines',
    'eu.veldsoft.no.thanks', 'com.sidhant.queens',
    'com.simondalvai.ball2box', 'xyz.deepdaikon.quinb',
    'org.secuso.privacyfriendlybattleship',
    'crypto.o0o0o0o0o.games.blackjack',
]
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
# 13 fresh titles (never run on this binary; baseline = first observation)
FRESH = [
    'app.halma', 'com.astroloop.game', 'com.jeffliu.balancetheball',
    'com.rocket9labs.boxcars', 'com.vayunmathur.games.solitaire',
    'com.vovagorodok.blichess', 'de.tobiasbielefeld.solitaire',
    'io.github.aoc_normal', 'io.github.hathibelagal.mykanji',
    'me.river.nightbell', 'page.codeberg.lanticy.guandan',
    'se.tube42.p9.android', 'si.palcka.tarok',
]
TITLES = KNOWN + FRESH

ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'C_TEXT_ON_FLAT': 1,
         'B_STRUCTURED': 2, 'A_RICH': 3}
STAGE_NAMES = ['S0_INSTALL_FAIL', 'S1_RUN_LAUNCHED', 'S2_ROUTE_DECIDED',
               'S3_ACTIVITY_LIFECYCLE', 'S4_SUBSYSTEM_LOADED',
               'S5_RENDER_PRODUCED', 'S6_SETTLED_FACE_TIERED']

SUBSYS_PATTERNS = [
    ('flutter', r'dlopen.*libflutter|libflutter\.so'),
    ('godot', r'dlopen.*libgodot|godot.*onCreate|GodotEngine'),
    ('webview', r'dlopen.*webview|WebViewNode|chromium'),
    ('compose', r'Compose|compose'),
    ('gles', r'eglCreateContext|glGetString|GLESv2'),
    ('dalvik', r'dalvikvm|DexFile|dexopt|real-dalvik'),
]
CHAIN_PATTERNS = [
    ('jni_onload', r'JNI_OnLoad'),
    ('register_natives', r'RegisterNatives'),
    ('activity_oncreate', r'onCreate'),
    ('fortify_chk', r'_chk'),
    ('looper', r'ALooper|epoll'),
]


def stage_of(res, log):
    """Honest loading-chain stage from run result + console log."""
    if res.get('status') == 'INSTALL_FAIL':
        return 0
    if not log:
        return 1
    s = 1
    if any(l.startswith('[ROUTE] DECISION') for l in log.splitlines()):
        s = 2
    if re.search(r'onCreate', log):
        s = 3
    subsys = sorted({n for n, p in SUBSYS_PATTERNS
                     if re.search(p, log, re.I)})
    if subsys:
        s = 4
    if res.get('screenshot_ok') or res.get('face') or \
       res.get('unique_colors') is not None:
        s = 5
    if res.get('timed_face') or res.get('tier'):
        s = 6
    return s


def chain_markers(log):
    out = {}
    for n, p in CHAIN_PATTERNS:
        out[f'n_{n}'] = len(re.findall(p, log, re.I))
    out['subsystems'] = sorted({nm for nm, p in SUBSYS_PATTERNS
                                if re.search(p, log, re.I)})
    out['bionic_abort'] = len(re.findall(r'BIONIC-ABORT|bionic abort', log, re.I))
    out['fatal_marks'] = len(re.findall(r'FATAL|Uncaught|uncaught exception', log, re.I))
    return out


def main():
    partial = w2.OUT / 'W13_BATTERY.partial.json'
    done = {}
    if partial.exists():
        try:
            for r in json.loads(partial.read_text()):
                done[r['pkg']] = r
        except Exception:
            pass
    results, drops = [], []
    for t in TITLES:
        if t in done:
            results.append(done[t])
            print('==', t, '(cached)', flush=True)
            continue
        print('==', t, flush=True)
        apk = BASE / f'upload/stuck_apks/{t}.apk'
        if not apk.exists():
            r = dict(pkg=t, status='NO_APK', stage=0,
                     stage_name=STAGE_NAMES[0])
            results.append(r)
            print('  NO_APK', flush=True)
            continue
        t0 = time.time()
        try:
            r = w2.run_one(t, str(apk))
        except Exception as e:
            traceback.print_exc()
            r = dict(pkg=t, status='RUN_ERR', error=str(e)[:300])
        r['wall_s'] = round(time.time() - t0, 1)
        log_path = w2.OUT / f'{t}.console.log'
        log = log_path.read_text(errors='ignore') if log_path.exists() else ''
        r['route_decision'] = [l for l in log.splitlines()
                               if l.startswith('[ROUTE] DECISION')]
        r['route_violation'] = [l for l in log.splitlines()
                                if 'ROUTE_VIOLATION' in l]
        r['route_surprise'] = [l for l in log.splitlines()
                               if 'ROUTE_SURPRISE' in l][:3]
        r.update(chain_markers(log))
        r['stage'] = stage_of(r, log)
        r['stage_name'] = STAGE_NAMES[r['stage']]
        tier = r.get('tier') or (r.get('timed_face') or {}).get('tier')
        r['tier'] = tier
        r['face'] = str(r['face']) if r.get('face') else None
        if t in FLOOR:
            r['floor'] = FLOOR[t]
            if tier in ORDER and FLOOR[t] in ORDER and \
               ORDER[tier] < ORDER[FLOOR[t]]:
                drops.append(dict(pkg=t, tier=tier, floor=FLOOR[t]))
            r['regression'] = (tier in ORDER and
                               ORDER[tier] >= ORDER[FLOOR[t]])
        else:
            r['regression'] = None  # fresh title: baseline creation
        results.append(r)
        print('  stage=', r['stage_name'], 'tier=', tier,
              'uncaught=', r.get('fatal_marks'), 'wall=', r['wall_s'],
              flush=True)
        # incremental persistence
        with open(partial, 'w') as f:
            json.dump(results, f, indent=1)
    (w2.OUT / 'W13_BATTERY.json').write_text(json.dumps(results, indent=1))
    print('DROPS:', drops)
    print('BATTERY', 'CLEAN' if not drops else f'REGRESSION x{len(drops)}')

if __name__ == '__main__':
    main()
