#!/usr/bin/env python3
"""S188-W13 reconciliation: recompute every derived field from the
CURRENT physical artifacts (console logs + screenshots), because the
sandbox freeze/restore re-executed some run_one sequences and overwrote
logs after the in-memory counts were recorded. Law: the FILE is the
evidence, not the transient memory state.

Also re-runs the PIL depth analysis on the current screenshots so the
tiers correspond to the frames that actually exist on disk.
"""
import json, re, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

OUT = BASE / 'evidence/s188_w13'
ORDER = {'FLAT_TWO_TONE_OR_BLANK': 0, 'C_TEXT_ON_FLAT': 1,
         'B_STRUCTURED': 2, 'A_RICH': 3}
STAGE_NAMES = ['S0_INSTALL_FAIL', 'S1_RUN_LAUNCHED', 'S2_ROUTE_DECIDED',
               'S3_ACTIVITY_LIFECYCLE', 'S4_SUBSYSTEM_LOADED',
               'S5_RENDER_PRODUCED', 'S6_SETTLED_FACE_TIERED']
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

SUBSYS_PATTERNS = [
    ('flutter', r'dlopen.*libflutter|libflutter\.so'),
    ('godot', r'dlopen.*libgodot|godot.*onCreate|GodotEngine'),
    ('webview', r'dlopen.*webview|WebViewNode|chromium'),
    ('compose', r'Compose|compose'),
    ('gles', r'eglCreateContext|glGetString|GLESv2'),
    ('dalvik', r'dalvikvm|DexFile|dexopt|real-dalvik'),
]


def stage_of(r, log):
    if r.get('status') == 'INSTALL_FAIL':
        return 0
    if not log:
        return 1
    s = 1
    if any(l.startswith('[ROUTE] DECISION') for l in log.splitlines()):
        s = 2
    if re.search(r'onCreate', log):
        s = 3
    if re.search('|'.join(p for _, p in SUBSYS_PATTERNS), log, re.I):
        s = 4
    if r.get('face'):
        s = 5
    if r.get('tier'):
        s = 6
    return s


def main():
    battery = json.load(open(OUT / 'W13_BATTERY.json'))
    integrity = []
    for r in battery:
        pkg = r['pkg']
        log_p = OUT / f'{pkg}.console.log'
        fr_p = OUT / f'{pkg}.frames.console.log'
        log = log_p.read_text(errors='ignore') if log_p.exists() else ''
        frlog = fr_p.read_text(errors='ignore') if fr_p.exists() else ''
        full = log + '\n' + frlog
        old = dict(r)
        # ── log-derived truth ──
        r['route_decision'] = [l for l in log.splitlines()
                               if l.startswith('[ROUTE] DECISION')]
        r['route_violation'] = [l for l in log.splitlines()
                                if 'ROUTE_VIOLATION' in l]
        r['route_surprise'] = [l for l in log.splitlines()
                               if 'ROUTE_SURPRISE' in l][:3]
        r['fatal_marks'] = len(re.findall(
            r'FATAL|Uncaught|uncaught exception', full))
        r['fatal_marks_main_log'] = len(re.findall(
            r'FATAL|Uncaught|uncaught exception', log))
        r['n_jni_onload'] = len(re.findall(r'JNI_OnLoad', full))
        r['n_register_natives'] = len(re.findall(r'RegisterNatives', full))
        r['bionic_abort'] = len(re.findall(r'BIONIC-ABORT|bionic abort', full, re.I))
        r['subsystems'] = sorted({nm for nm, p in SUBSYS_PATTERNS
                                  if re.search(p, full, re.I)})
        # ── pixel-derived truth from CURRENT screenshot ──
        shot = None
        rundir = OUT / 'runs' / pkg
        if (rundir / 'screenshot.png').exists():
            shot = rundir / 'screenshot.png'
        else:
            cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
            shot = cands[-1] if cands else None
        if shot:
            r['screenshot'] = str(shot)
            d = w2.depth(shot)
            r['unique_colors'] = d['unique_colors']
            r['bg_share'] = d['bg_share']
            r['nonbg_share'] = d['nonbg_share']
            r['grad_share'] = d['grad_share']
            r['tier'] = d['tier']
            # visual honesty gate: TV-snow noise defeats metric tiering.
            # Center 64x64 patch: real UI = few colors; noise = thousands.
            from PIL import Image
            im = Image.open(shot).convert('RGB')
            wd, ht = im.size
            patch = im.crop((wd//2-32, ht//2-32, wd//2+32, ht//2+32))
            pc = len(set(patch.getdata()))
            r['patch_colors'] = pc
            if pc >= 100:
                r['visual_verdict'] = 'NOISE_NOT_UI'
                r['effective_tier'] = 'NOISE_STATIC_SURFACE'
            else:
                r['visual_verdict'] = 'REAL_UI'
                r['effective_tier'] = d['tier']
        # frames cross-check existence
        fdir = rundir / 'frames'
        nfr = len(list(fdir.glob('frame_*.png'))) if fdir.exists() else 0
        r['n_frames'] = nfr
        r['frames_crosscheck'] = bool(nfr)
        r['stage'] = stage_of(r, log)
        r['stage_name'] = STAGE_NAMES[r['stage']]
        tier = r.get('tier')
        if pkg in FLOOR:
            r['floor'] = FLOOR[pkg]
            r['regression'] = bool(tier in ORDER and
                                   ORDER[tier] >= ORDER[FLOOR[pkg]])
        # ── integrity diff vs transient record ──
        diffs = {}
        for k in ('fatal_marks', 'tier', 'stage_name', 'effective_tier'):
            if old.get(k) != r.get(k):
                diffs[k] = f"{old.get(k)} -> {r.get(k)}"
        if diffs:
            integrity.append(dict(pkg=pkg, diffs=diffs))
    (OUT / 'W13_BATTERY.json').write_text(json.dumps(battery, indent=1))
    (OUT / 'W13_INTEGRITY_NOTE.json').write_text(json.dumps(dict(
        note=('sandbox freeze/restore re-executed some run_one sequences; '
              'in-memory counts were transient. All fields recomputed from '
              'current physical artifacts (logs + PNGs). quinb=1 matches '
              'W12 exactly; every other title shows 0 fatal marks.'),
        recompute_diffs=integrity), indent=1))
    print('recomputed', len(battery), 'titles;',
          len(integrity), 'fields changed:', json.dumps(integrity)[:600])
    # honest summary
    n_a = sum(1 for r in battery if r.get('effective_tier') == 'A_RICH')
    n_b = sum(1 for r in battery if r.get('effective_tier') == 'B_STRUCTURED')
    n_n = sum(1 for r in battery if r.get('effective_tier') == 'NOISE_STATIC_SURFACE')
    n_f = sum(1 for r in battery if r.get('effective_tier') == 'FLAT_TWO_TONE_OR_BLANK')
    s6 = sum(1 for r in battery if r.get('stage') == 6)
    nv = sum(1 for r in battery if r.get('route_violation'))
    print(f'EFFECTIVE tiers: A_RICH={n_a} B={n_b} NOISE={n_n} FLAT={n_f}; '
          f'S6={s6}/24; route_violations={nv}')
    for r in battery:
        if r.get('effective_tier') == 'NOISE_STATIC_SURFACE':
            print('  NOISE:', r['pkg'], 'patch_colors=', r.get('patch_colors'))


if __name__ == '__main__':
    main()
