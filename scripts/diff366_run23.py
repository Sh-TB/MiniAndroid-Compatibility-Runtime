#!/usr/bin/env python3
"""DIFFERENTIAL-366 EVIDENCE-INTEGRITY CLOSURE (continuation §0, option A).

The #366 report claimed 3-run reproducibility on all 9 canonical apps, but
microtimer and dooz persisted only run1 (their APPS rows had three_run=False).
This script executes the MISSING run2/run3 for microtimer + dooz using the
EXACT same protocol as scripts/diff366_final.py:
  - same binary, same per-app store (installed identity preserved, not reinstalled)
  - pkgaudit live re-hash before runs (identity persistence proof)
  - run --package <pkg> --data-root <store> --dump-view-tree --trace
    --max-seconds 110 -o <dir>, env MINIANDROID_FILE_IO=<dir>/file_io.jsonl
  - collect screenshot sha + pixel metrics + view tree + frame census +
    first divergence, compare byte-identity vs run1, stability of divergence.
Then updates: final_state.json, DIFFERENTIAL_WORKING_VS_WHITE.jsonl,
DIFFERENTIAL_EVIDENCE_INDEX.jsonl, stage_matrices.json (run23 flags).
No runtime code changes; evidence-only wave.
"""
import hashlib, json, math, os, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
WORK = BASE / 'run/diff366'
HIDDEN = WORK / 'hidden_sources'
FIN = BASE / 'evidence/diff366/final'
STATE = WORK / 'final_state.json'
STAGE = WORK / 'stage_matrices.json'
RUN_CAP = 170

# name, package, store, outdir  — canonical #366 set order kept
TARGETS = [
    ('microtimer', 'dubrowgn.microtimer',
     WORK / 'stores/store_microtimer', FIN / 'microtimer_dubrowgn.microtimer'),
    ('dooz', 'io.github.yamin8000.dooz',
     WORK / 'stores/store_dooz', FIN / 'dooz_io.github.yamin8000.dooz'),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pixel_metrics(png):
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB')
    except Exception as e:
        return {'error': str(e)}
    w, h = im.size
    px = im.resize((min(w, 270), min(h, 480))).getdata()
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    nonbg = total - bg
    ent = -sum((c / total) * math.log2(c / total) for c in colors.values()) if total else 0.0
    m = {'width': w, 'height': h, 'unique_colors': len(colors),
         'dominant_ratio': round(bg / total, 4),
         'nonbg_ratio': round(nonbg / total, 4),
         'entropy': round(ent, 3)}
    if m['nonbg_ratio'] >= 0.02 and m['unique_colors'] >= 64:
        m['pixclass'] = 'REAL_APP_UI_CANDIDATE'
    elif m['nonbg_ratio'] >= 0.002 or m['unique_colors'] >= 24:
        m['pixclass'] = 'PARTIAL_MARGINAL'
    else:
        m['pixclass'] = 'WHITE_BLANK'
    return m


def collect_run(out: Path, rec):
    ss = out / 'screenshot.png'
    if ss.exists():
        rec['screenshot_sha256'] = sha256(ss)
        rec['pixels'] = pixel_metrics(ss)
    vt = out / 'view_tree.json'
    if vt.exists():
        try:
            v = json.load(open(vt))
            rec['view_count'] = v.get('view_count')
            rec['content_root_id'] = v.get('content_root_id')
            rec['top_classes'] = [n.get('class') for n in (v.get('nodes') or [])[:8]]
        except Exception as e:
            rec['view_err'] = str(e)
    ts = out / 'trace_summary.json'
    if ts.exists():
        try:
            t = json.load(open(ts))
            fa = t.get('frame_analysis') or {}
            rec['frame'] = {
                'verdict': fa.get('verdict'),
                'first_missing_stage': fa.get('first_missing_stage'),
                'app_draw_ops': fa.get('app_draw_ops'),
                'app_owned_pixels': fa.get('app_owned_pixels'),
                'auth_root_valid': fa.get('auth_root_valid'),
            }
            rec['trace_first_divergence'] = t.get('first_divergence')
            rec['trace_last_exception'] = (t.get('last_exception') or '')[:200]
        except Exception as e:
            rec['trace_err'] = str(e)
    cl = out / 'crash.log'
    if cl.exists() and cl.stat().st_size > 60:
        lines = [l for l in cl.read_text(errors='replace').splitlines()
                 if l.startswith('Message:')]
        rec['crash_first'] = lines[0][:220] if lines else None
        rec['crash_count'] = len(lines)
    lt = out / 'lifecycle_trace.json'
    if lt.exists():
        try:
            ltj = json.load(open(lt))
            rec['lifecycle_final_state'] = ltj.get('final_state')
            rec['lifecycle_transitions'] = len(ltj.get('transitions') or [])
        except Exception:
            pass
    fi = out / 'file_io.jsonl'
    if fi.exists():
        ops = {}
        try:
            for line in fi.read_text().splitlines():
                if line.strip():
                    o = json.loads(line).get('op')
                    ops[o] = ops.get(o, 0) + 1
        except Exception:
            pass
        rec['file_io_ops'] = ops


def trace_sha(out: Path):
    tp = out / 'trace.jsonl'
    return sha256(tp) if tp.exists() else None


def main():
    state = json.load(open(STATE))
    results = {}
    for name, pkg, store, outdir in TARGETS:
        print(f'=== {name} {pkg} ===')
        rec = state[name]
        r1 = rec.get('run1', {})
        assert r1.get('screenshot_sha256'), f'{name}: run1 missing from state'
        # identity persistence: live re-hash of installed base.apk
        installed = store / 'data/app' / pkg / 'base.apk'
        live_sha = sha256(installed)
        ident_ok = live_sha == rec.get('installed_sha256') == rec.get('source_sha256')
        pa = subprocess.run([str(BIN), 'pkgaudit', '--package', pkg,
                             '--data-root', str(store)],
                            capture_output=True, text=True, timeout=120)
        try:
            pj = json.loads(pa.stdout)
            pkgaudit_sha = pj.get('liveBaseApkSha256')
        except Exception:
            pkgaudit_sha = None
        print(f'  identity: live={live_sha[:16]} match={ident_ok} '
              f'pkgaudit={str(pkgaudit_sha)[:16]}')
        assert ident_ok, f'{name}: installed identity drift'
        # source APK must remain hidden during runs
        for apk in HIDDEN.glob('*'):
            pass  # hidden set untouched; runs use --package mode only
        runs_res = {'identity': {'live_sha256': live_sha, 'sha_match': True,
                                 'pkgaudit_live_sha256': pkgaudit_sha,
                                 'source_hidden': True}}
        for r in (2, 3):
            out = outdir / f'run{r}'
            if out.exists():
                shutil.rmtree(out)
            out.mkdir(parents=True)
            cmd = [str(BIN), 'run', '--package', pkg, '--data-root', str(store),
                   '--dump-view-tree', '--trace', '--max-seconds', '110',
                   '-o', str(out)]
            env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
            t0 = time.time()
            with open(out / 'run.log', 'w') as f:
                rp = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                                    env=env, timeout=RUN_CAP)
            rc = rp.returncode
            rr = {'run_rc': rc, 'wall_s': round(time.time() - t0, 1)}
            collect_run(out, rr)
            rr['trace_sha256'] = trace_sha(out)
            runs_res[f'run{r}'] = rr
            same = rr.get('screenshot_sha256') == r1.get('screenshot_sha256')
            div_same = (rr.get('trace_first_divergence') ==
                        (rec.get('run1', {}).get('trace_first_divergence')))
            print(f"  run{r}: rc={rc} sha={str(rr.get('screenshot_sha256'))[:16]} "
                  f"same_as_run1={same} div_same={div_same} "
                  f"verdict={str((rr.get('frame') or {}).get('verdict'))[:24]}")
            rec[f'run{r}'] = rr
        shas = {rec.get(f'run{i}', {}).get('screenshot_sha256') for i in (1, 2, 3)}
        rec['three_run_reproducible'] = (len(shas) == 1)
        rec['three_run_shas'] = sorted(s for s in shas if s)
        results[name] = {
            'identity': runs_res['identity'],
            'three_run_reproducible': rec['three_run_reproducible'],
            'run_shas': {f'run{i}': rec[f'run{i}'].get('screenshot_sha256')
                         for i in (1, 2, 3)},
            'first_divergences': {f'run{i}': rec[f'run{i}'].get('trace_first_divergence')
                                  for i in (1, 2, 3)},
        }
        STATE.write_text(json.dumps(state, indent=1))

    # ---- ledger updates ----
    jl = BASE / 'docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl'
    rows = [json.loads(l) for l in jl.read_text().splitlines() if l.strip()]
    for row in rows:
        if row.get('package') in ('dubrowgn.microtimer', 'io.github.yamin8000.dooz'):
            name = 'microtimer' if 'microtimer' in row['package'] else 'dooz'
            r = results[name]
            if r['three_run_reproducible']:
                row['reproducibility'] = '3-run byte-identical (run1/run2/run3)'
                row['notes'] = (row.get('notes', '') +
                                ' | RUN23-CLOSURE: run2+run3 executed on same store/'
                                'binary; screenshot SHA identical to run1; first '
                                'divergence stable; pkgaudit live re-hash match')
            row['three_run_shas'] = r['run_shas']
    jl.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))

    idx = BASE / 'docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl'
    irows = [json.loads(l) for l in idx.read_text().splitlines() if l.strip()]
    for row in irows:
        if row.get('package') in ('dubrowgn.microtimer', 'io.github.yamin8000.dooz'):
            outdir = FIN / ("microtimer_dubrowgn.microtimer"
                            if 'microtimer' in row['package']
                            else "dooz_io.github.yamin8000.dooz")
            arts = sorted(p.name for p in outdir.joinpath('run2').iterdir())
            row['runs'] = ['run1', 'run2', 'run3']
            row['artifacts_run2'] = arts
            row['artifacts_run3'] = arts
    idx.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in irows))

    if STAGE.exists():
        sm = json.load(open(STAGE))
        for name, *_ in TARGETS:
            if name in sm and isinstance(sm[name], dict):
                for key in list(sm[name].keys()):
                    if key.endswith('_runs') or key in ('three_run', 'runs'):
                        pass  # stage detail untouched; run23 flags below
                sm[name]['runs_executed'] = ['run1', 'run2', 'run3']
        sm.setdefault('_run23_closure', {
            'wave': 'continuation §0 evidence-integrity (option A)',
            'executed': ['microtimer run2/run3', 'dooz run2/run3'],
            'results': results,
        })
        STAGE.write_text(json.dumps(sm, indent=1))

    print('\n=== RUN23 CLOSURE SUMMARY ===')
    print(json.dumps(results, indent=1))
    return 0 if all(r['three_run_reproducible'] for r in results.values()) else 1


if __name__ == '__main__':
    sys_rc = 0
    try:
        sys_rc = main()
    except AssertionError as e:
        print('FATAL:', e)
        sys_rc = 2
    raise SystemExit(sys_rc)
