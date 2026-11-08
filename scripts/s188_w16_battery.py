#!/usr/bin/env python3
"""S188-W16: CODER-PROGRESS battery EXTENSION (user directive: "ادامه
چند ده تسک با هم انجام بده، حداقل ۲۰ مورد، کدرها هم پیشرفت داشتن" —
do dozens of tasks together, at least 20 items; the coders have also
made progress).

17 titles NEVER battery-run on this lineage (W2/W12/W13 batteries
covered 24 titles); this wave extends battery coverage to the FULL
41-title stuck_apks corpus on the W15-final binary
50400036a6f16fe8. Same loading-chain stage law (S0..S6, identical
patterns as s188_w13_battery), same run_one, same --trace sequence.

Incremental persistence: every finished title is appended to
W16_BATTERY.partial.json so a sandbox recycle never loses runs
(W13 lesson: files are the evidence, memory is transient).
"""
import json, sys, re, time, traceback
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w16'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

# 17 fresh titles = corpus minus the 24 battery-run titles (W2/W12/W13)
NEW = [
    'bim.app', 'com.bupkis.tirailleur', 'com.clavierhaus.gnubg',
    'com.eightsines.firestrike.opensource', 'com.hegocre.nextcloudpasswords',
    'com.hfut.schedule', 'com.newsblur', 'com.vovagorodok.blidraughts',
    'de.seemoo.at_tracking_detection', 'de.taz.android.app.free',
    'foehnix.widget', 'io.timelimit.android.aosp.direct', 'me.timeto.app',
    'org.nitri.opentopo', 'org.opensurge2d.surgeengine',
    'ru.wohlsoft.thextech.fdroid', 'site.leos.apps.lespas',
]
TITLES = NEW

ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'C_TEXT_ON_FLAT': 1,
         'B_STRUCTURED': 2, 'A_RICH': 3}
STAGE_NAMES = ['S0_INSTALL_FAIL', 'S1_RUN_LAUNCHED', 'S2_ROUTE_DECIDED',
               'S3_ACTIVITY_LIFECYCLE', 'S4_SUBSYSTEM_LOADED',
               'S5_RENDER_PRODUCED', 'S6_SETTLED_FACE_TIERED']

# identical stage law to s188_w13_battery.py (verbatim patterns)
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
    partial = w2.OUT / 'W16_BATTERY.partial.json'
    done = {}
    if partial.exists():
        try:
            for r in json.loads(partial.read_text()):
                done[r['pkg']] = r
        except Exception:
            pass
    results = []
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
        r['regression'] = None  # fresh title: baseline creation
        results.append(r)
        print('  stage=', r['stage_name'], 'tier=', tier,
              'uncaught=', r.get('fatal_marks'), 'wall=', r['wall_s'],
              flush=True)
        with open(partial, 'w') as f:
            json.dump(results, f, indent=1)
    (w2.OUT / 'W16_BATTERY.json').write_text(json.dumps(results, indent=1))
    n6 = sum(1 for r in results if r.get('stage') == 6)
    viol = sum(len(r.get('route_violation') or []) for r in results)
    print(f'W16 battery: {len(results)} titles, stage6={n6}, '
          f'ROUTE_VIOLATION={viol}')

if __name__ == '__main__':
    main()
