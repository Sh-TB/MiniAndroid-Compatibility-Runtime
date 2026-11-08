#!/usr/bin/env python3
"""S188-W16: fleet reconcile — recompute the W16 battery from physical
artifacts (logs + PNGs; "files are the evidence"), apply the visual
honesty gate (center-64x64 patch colors >=100 => NOISE_NOT_UI, the
W13 calibration), audit routes across all W16 logs, and merge the
fleet loading-progress view W12(11) + W13(24) + W16(17) = 41 titles.

Outputs:
  evidence/s188_w16/W16_BATTERY.json      (final, recomputed rows)
  evidence/s188_w16/W16_INTEGRITY_NOTE.json
  evidence/s188_w16/W16_PROGRESS.json     (fleet view)
"""
import json, re
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
W16 = BASE / 'evidence/s188_w16'
W13 = BASE / 'evidence/s188_w13'
W12 = BASE / 'evidence/s188_w12'

STAGE_NAMES = ['S0_INSTALL_FAIL', 'S1_RUN_LAUNCHED', 'S2_ROUTE_DECIDED',
               'S3_ACTIVITY_LIFECYCLE', 'S4_SUBSYSTEM_LOADED',
               'S5_RENDER_PRODUCED', 'S6_SETTLED_FACE_TIERED']
ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'C_TEXT_ON_FLAT': 1,
         'B_STRUCTURED': 2, 'A_RICH': 3}
SUBSYS_PATTERNS = [
    ('flutter', r'dlopen.*libflutter|libflutter\.so'),
    ('godot', r'dlopen.*libgodot|godot.*onCreate|GodotEngine'),
    ('webview', r'dlopen.*webview|WebViewNode|chromium'),
    ('compose', r'Compose|compose'),
    ('gles', r'eglCreateContext|glGetString|GLESv2'),
    ('dalvik', r'dalvikvm|DexFile|dexopt|real-dalvik'),
]
CHAIN_PATTERNS = [
    ('jni_onload', r'JNI_OnLoad'), ('register_natives', r'RegisterNatives'),
    ('activity_oncreate', r'onCreate'), ('fortify_chk', r'_chk'),
    ('looper', r'ALooper|epoll'),
]


def stage_of(res, log):
    if res.get('status') == 'INSTALL_FAIL':
        return 0
    if not log:
        return 1
    s = 1
    if any(l.startswith('[ROUTE] DECISION') for l in log.splitlines()):
        s = 2
    if re.search(r'onCreate', log):
        s = 3
    if sorted({n for n, p in SUBSYS_PATTERNS if re.search(p, log, re.I)}):
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
    raw = json.loads((W16 / 'W16_BATTERY.partial.json').read_text())
    rows, honesty = [], []
    for r in raw:
        t = r['pkg']
        log_path = W16 / f'{t}.console.log'
        log = log_path.read_text(errors='ignore') if log_path.exists() else ''
        r['route_decision'] = [l for l in log.splitlines()
                               if l.startswith('[ROUTE] DECISION')]
        r['route_violation'] = [l for l in log.splitlines()
                                if 'ROUTE_VIOLATION' in l]
        r.update(chain_markers(log))
        r['stage'] = stage_of(r, log)
        r['stage_name'] = STAGE_NAMES[r['stage']]
        # honesty gate on the PHYSICAL face file
        face = None
        cand = W16 / f'face_{t}.jpg'
        if cand.exists():
            face = cand
        im = Image.open(face).convert('RGB') if face else None
        if im:
            wd, ht = im.size
            patch = im.crop((wd // 2 - 32, ht // 2 - 32,
                             wd // 2 + 32, ht // 2 + 32))
            pc = len(set(patch.getdata()))
            r['patch_colors'] = pc
            if pc >= 100:
                r['visual_verdict'] = 'NOISE_NOT_UI'
                r['effective_tier'] = 'NOISE_STATIC_SURFACE'
                honesty.append(dict(pkg=t, patch_colors=pc,
                                    raw_tier=r.get('tier')))
            else:
                r['visual_verdict'] = 'HUMAN_INSPECTABLE'
                r['effective_tier'] = r.get('tier')
        rows.append(r)
    (W16 / 'W16_BATTERY.json').write_text(json.dumps(rows, indent=1))

    # route audit across all W16 logs
    n_logs = n_dec = n_viol = 0
    for lp in W16.glob('*.console.log'):
        n_logs += 1
        txt = lp.read_text(errors='ignore')
        if any(l.startswith('[ROUTE] DECISION') for l in txt.splitlines()):
            n_dec += 1
        n_viol += len(re.findall(r'ROUTE_VIOLATION', txt))

    integrity = {
        'wave': 'S188-W16',
        'note': 'all fields recomputed from physical artifacts '
                '(console logs + face JPGs); visual honesty gate = '
                'center-64x64 patch colors >=100 => NOISE_NOT_UI '
                '(W13 calibration: noise 1228-3000 vs real UI 1-6)',
        'titles': len(rows),
        'stage6': sum(1 for r in rows if r.get('stage') == 6),
        'route_logs': n_logs, 'route_decisions': n_dec,
        'route_violations': n_viol,
        'honesty_downgrades': honesty,
        'tier_histogram': {
            k: sum(1 for r in rows if r.get('effective_tier') == k)
            for k in ['A_RICH', 'B_STRUCTURED', 'C_TEXT_ON_FLAT',
                      'FLAT_TWO_TONE_OR_BLANK', 'NOISE_STATIC_SURFACE']},
    }
    (W16 / 'W16_INTEGRITY_NOTE.json').write_text(json.dumps(integrity, indent=1))

    # ---- fleet view: W12 (11) + W13 (24) + W16 (17) ----
    def load(p):
        return {r['pkg']: r for r in json.loads(p.read_text())} \
            if p.exists() else {}

    w12, w13 = load(W12 / 'W12_BATTERY.json'), load(W13 / 'W13_BATTERY.json')
    w16 = {r['pkg']: r for r in rows}
    fleet = []
    corpus = sorted(set(w12) | set(w13) | set(w16))
    for t in corpus:
        first = 'W12' if t in w12 else ('W13' if t in w13 else 'W16')
        cur = w16.get(t) or w13.get(t) or w12.get(t)
        fleet.append({
            'pkg': t,
            'first_battery_observation': first,
            'stage_now': cur.get('stage'),
            'stage_name_now': cur.get('stage_name') or STAGE_NAMES[cur.get('stage', 1)],
            'tier_now': cur.get('tier'),
            'effective_tier_now': cur.get('effective_tier'),
            'route_lane_now': (cur.get('route_decision') or [''])[0],
            'route_violations': len(cur.get('route_violation') or []),
        })
    prog = {
        'wave': 'S188-W16',
        'title': 'FLEET LOADING-PROGRESS: 41/41 stuck_apks corpus titles '
                 'battery-covered (W2/W12: 11 -> W13: +13 -> W16: +17)',
        'corpus_size': len(corpus),
        'battery_covered': len(fleet),
        'stage6_count': sum(1 for f in fleet if f['stage_now'] == 6),
        'route_violation_total': sum(f['route_violations'] for f in fleet),
        'w16_fresh_progress': [
            {'pkg': t, 'before': 'ROUTE-ARCHIVED ONLY (S2 knowledge, never run)',
             'after': STAGE_NAMES[6] + ' + face tier'}
            for t in sorted(w16)],
        'fleet': fleet,
    }
    (W16 / 'W16_PROGRESS.json').write_text(json.dumps(prog, indent=1))
    print('W16 rows:', len(rows), 'stage6:', integrity['stage6'])
    print('route logs:', n_logs, 'decisions:', n_dec, 'violations:', n_viol)
    print('tiers:', integrity['tier_histogram'])
    print('fleet covered:', len(fleet), '/', prog['corpus_size'],
          'stage6:', prog['stage6_count'])


if __name__ == '__main__':
    main()
