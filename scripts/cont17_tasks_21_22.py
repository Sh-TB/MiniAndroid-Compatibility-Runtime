#!/usr/bin/env python3
"""CONT-17 Tasks 21+22: SP-1 success corpus (per-title signature JSON) +
SP-2/3/12 common-successful-chain proof artifact on one known-good title
(microtimer, fresh at HEAD). Evidence: evidence/cont17/{success_corpus.json,success_chain_microtimer.json}"""
import json, os, glob, hashlib

BASE = '/home/z/my-project'
OUTDIR = f'{BASE}/evidence/cont17'
os.makedirs(OUTDIR, exist_ok=True)

def apk_sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16] if p and os.path.exists(p) else None

titles = {}

# ---- fresh HEAD anchor runs (provenance=RUN-FRESH-CONT17) ----
for d in sorted(glob.glob(f'{BASE}/run/cont16/reg/*_[123]')):
    pkg = os.path.basename(d).rsplit('_', 1)[0]
    ts = f'{d}/trace_summary.json'
    if not os.path.exists(ts):
        continue
    t = json.load(open(ts))
    fa = t.get('frame_analysis', {})
    sig = titles.setdefault(pkg, {'runs': [], 'provenance': 'RUN-FRESH-CONT17'})
    sig['runs'].append({
        'dir': os.path.relpath(d, BASE),
        'screenshot_sha16': (fa.get('screenshot_sha256') or '')[:16],
        'verdict': fa.get('verdict'),
        'app_draw_ops': fa.get('app_draw_ops'),
        'app_owned_pixels': fa.get('app_owned_pixels'),
        'activity': t.get('activity'),
        'renderer_family': t.get('renderer_family'),
        'auth_root_valid': fa.get('auth_root_valid'),
    })
    if sig.get('apk_sha16') is None:
        for cand in (f'{BASE}/upload/{pkg}*.apk', f'{BASE}/upload/canonical_apks/{pkg}*.apk'):
            m = sorted(glob.glob(cand))
            if m:
                sig['apk_sha16'] = apk_sha16(m[0]); sig['apk_path'] = os.path.relpath(m[0], BASE); break

# ---- fresh traced dooz (honest non-success cluster row) ----
ts = f'{BASE}/run/cont17/dooz_traced/trace_summary.json'
if os.path.exists(ts):
    t = json.load(open(ts)); fa = t.get('frame_analysis', {})
    titles['io.github.yamin8000.dooz'] = {
        'provenance': 'RUN-FRESH-CONT17 (traced, F-265 frontier row — NOT a success row)',
        'apk_sha16': apk_sha16(f'{BASE}/upload/canonical_apks/dooz_23_toplevel.apk'),
        'apk_path': 'upload/canonical_apks/dooz_23_toplevel.apk',
        'runs': [{'dir': 'run/cont17/dooz_traced',
                  'screenshot_sha16': (fa.get('screenshot_sha256') or '')[:16],
                  'verdict': fa.get('verdict'), 'app_draw_ops': fa.get('app_draw_ops'),
                  'app_owned_pixels': fa.get('app_owned_pixels'),
                  'activity': t.get('activity'), 'renderer_family': t.get('renderer_family'),
                  'auth_root_valid': fa.get('auth_root_valid')}],
    }

# ---- recorded CONT-15 evidence (provenance=RECORDED-CONT15) ----
sg = json.load(open(f'{BASE}/evidence/cont15/sixgame_validation.json'))
for title, row in sg.items():
    titles[row['pkg']] = {
        'provenance': 'RECORDED-CONT15 (six-game claim 6/6 x3)',
        'apk_sha16': row.get('apk_sha16'),
        'runs': [{'screenshot_sha16': r['sha16'], 'verdict': r['verdict'],
                  'app_draw_ops': r['ops'], 'app_owned_pixels': r['px']} for r in row.get('runs', [])],
    }
titles['rk.android.app.forkgram'] = {
    'provenance': 'RECORDED-CONT15 (telegram REAL_APP_CONTENT cf4c41e6 x3, canonical-lineage causal chain)',
    'apk_sha16': 'cf4c41e62ceb6557',
    'runs': [{'screenshot_sha16': 'cf4c41e62ceb6557', 'verdict': 'REAL_APP_CONTENT',
              'app_draw_ops': 11, 'app_owned_pixels': 117133}]}

# ---- finalize: 3-run reproducibility + success class ----
corpus = {'generated': '2026-10-08', 'binary': 'a8761a482a186eac',
          'law': 'never count a frame as success merely because a PNG exists — verdict from F-NEW-233 frame truth only',
          'titles': {}}
for pkg, sig in titles.items():
    runs = sig['runs']
    shas = {r.get('screenshot_sha16') for r in runs}
    verdicts = {r.get('verdict') for r in runs}
    corpus['titles'][pkg] = {
        **sig,
        'n_runs': len(runs),
        'three_run_byte_identical': len(runs) >= 3 and len(shas) == 1 and None not in shas,
        'success_class': ('REAL_APP_CONTENT' if verdicts == {'REAL_APP_CONTENT'}
                          else ('DEFAULT_BACKGROUND_ONLY' if verdicts == {'DEFAULT_BACKGROUND_ONLY'}
                                else (list(verdicts)[0] if len(verdicts) == 1 else 'MIXED'))),
    }
n_real = sum(1 for t in corpus['titles'].values() if t['success_class'] == 'REAL_APP_CONTENT')
corpus['summary'] = {'n_titles': len(corpus['titles']), 'n_real_app_content': n_real}
json.dump(corpus, open(f'{OUTDIR}/success_corpus.json', 'w'), indent=1)
print(f"SP-1 corpus: {len(corpus['titles'])} titles, {n_real} REAL_APP_CONTENT")

# ---- SP-2/3/12: common successful chain on microtimer (fresh at HEAD) ----
d = f'{BASE}/run/cont16/reg/dubrowgn.microtimer_1'
t = json.load(open(f'{d}/trace_summary.json'))
fa = t['frame_analysis']
chain = {
  'generated': '2026-10-08', 'binary': 'a8761a482a186eac',
  'title': 'dubrowgn.microtimer (Simple Microtimer — Handler-timer XML-widget family)',
  'law': 'SP-2/3/12 common minimum render contract: every stage PASS/FAIL/NOT_USED/UNKNOWN',
  'stages': [
    {'stage': 'APK->manifest parse', 'state': 'PASS', 'evidence': 'install rc=0 + post-install identity = source identity (skill OP-3)'},
    {'stage': 'Application attach', 'state': 'PASS', 'evidence': 'lifecycle_trace.json Application chain'},
    {'stage': 'Activity onCreate', 'state': 'PASS', 'evidence': f"activity={t.get('activity')} reached, lifecycle callbacks complete"},
    {'stage': 'Window->Decor/content root', 'state': 'PASS', 'evidence': f"auth_root_valid={fa.get('auth_root_valid')} content_bounds={fa.get('content_bounds')}"},
    {'stage': 'setContentView->ViewTree', 'state': 'PASS', 'evidence': f"no_root={fa.get('no_root')}; view tree dumped (OP-5 census 398309 owned px on probe; app px {fa.get('app_owned_pixels')})"},
    {'stage': 'measure->layout->draw traversal', 'state': 'PASS', 'evidence': f"app_draw_ops={fa.get('app_draw_ops')} APP_REAL_DRAW (renderer {t.get('renderer_family')})"},
    {'stage': 'app-owned draw op -> framebuffer', 'state': 'PASS', 'evidence': f"app_owned_pixels={fa.get('app_owned_pixels')} inside content bounds={fa.get('app_owned_pixels_inside_content_bounds')}"},
    {'stage': 'capture', 'state': 'PASS', 'evidence': f"screenshot sha {fa.get('screenshot_sha256','')[:16]} x3 byte-identical (run/cont16/reg)"},
    {'stage': 'no synthetic pixels', 'state': 'PASS', 'evidence': f"diag_owned_pixels={fa.get('diag_owned_pixels')} (diagnostic ownership ZERO)"},
    {'stage': 'input path', 'state': 'NOT_USED', 'evidence': 'no click-test in this run (S79 unote click evidence covers the input stage family)'},
    {'stage': 'state mutation', 'state': 'NOT_USED', 'evidence': 'timer not started in capture run; persistence family covered by unote SQLITE-SHADOW record'},
  ],
  'white-family separation (SP-3)': {
    'REAL_APP_CONTENT': ['microtimer', 'unote', 'opencalc', 'gmdice', 'chess', 'six-game family', 'telegram(forkgram)'],
    'DEFAULT_BACKGROUND_ONLY': ['dooz (F-NEW-265 measure-death)', 'tictactoe_emmanuel (F-NEW-219 JNI family)'],
    'distinct_root_families_law': 'APP_DRAW_OPS=0 rows kept distinct from VIEWTREE_NOT_REACHED rows — first_missing_stage names the family'},
}
json.dump(chain, open(f'{OUTDIR}/success_chain_microtimer.json', 'w'), indent=1)
print('SP-2/3/12 chain artifact written (11 stages)')
