#!/usr/bin/env python3
"""CONT-366 ROOT-A fan-out — rerun the differential set on the patched
binary (Arrays.toString law + Class.newInstance/getModifiers/isMemberClass
laws) and record the NEXT first divergence per app.

Apps (continuation §3 ROOT-A list + differential set):
  asteroids, spacevertex (original ROOT-A failures)
  bouncy, opencalc, unote, microtimer (working set)
  dooz (Compose control), memory (AndroidX control)
Protocol: same stores (installed identity preserved), pkgaudit re-hash,
--package mode, --dump-view-tree --trace, screenshot SHA vs previous run.
"""
import hashlib, json, subprocess, os, shutil, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
FIN = BASE / 'evidence/diff366/final'
ROOTA = BASE / 'evidence/diff366/root_a'
RUN_CAP = 170

APPS = [
    ('asteroids', 'com.game.asteroids_revenge'),
    ('spacevertex', 'fr.arnaudguyon.spacevertex'),
    ('bouncy', 'com.dozingcatsoftware.bouncy'),
    ('opencalc', 'com.darkempire78.opencalculator'),
    ('unote', 'app.varlorg.unote'),
    ('microtimer', 'dubrowgn.microtimer'),
    ('dooz', 'io.github.yamin8000.dooz'),
    ('memory', 'com.sanskritbasics.memory'),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def first_divergence(out: Path):
    """sharpest available failure marker for the run"""
    log = out / 'run.log'
    if not log.exists():
        return None
    for line in log.read_text(errors='replace').splitlines():
        if '[THROWABLE-MSG]' in line or '[EXC-PROPAGATE]' in line:
            return line[:260]
    return None


def frame_verdict(out: Path):
    ts = out / 'trace_summary.json'
    if ts.exists():
        try:
            t = json.load(open(ts))
            fa = t.get('frame_analysis') or {}
            return fa.get('verdict'), fa.get('app_draw_ops')
        except Exception:
            pass
    return None, None


def main():
    ROOTA.mkdir(parents=True, exist_ok=True)
    results = {}
    prev_state = json.load(open(BASE / 'run/diff366/final_state.json'))
    for name, pkg in APPS:
        store = BASE / 'run/diff366/stores' / f'store_{name}'
        out = ROOTA / f'{name}_{pkg}'
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        pa = subprocess.run([str(BIN), 'pkgaudit', '--package', pkg,
                             '--data-root', str(store)],
                            capture_output=True, text=True, timeout=120)
        try:
            live = json.loads(pa.stdout).get('liveBaseApkSha256')
            ident = live == prev_state[name]['installed_sha256']
        except Exception:
            live, ident = None, False
        cmd = [str(BIN), 'run', '--package', pkg, '--data-root', str(store),
               '--dump-view-tree', '--trace', '--max-seconds', '110',
               '-o', str(out)]
        env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
        t0 = time.time()
        with open(out / 'run.log', 'w') as f:
            try:
                rp = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                                    env=env, timeout=RUN_CAP)
                rc = rp.returncode
            except subprocess.TimeoutExpired:
                rc = 'TIMEOUT'
        ss = out / 'screenshot.png'
        sha = sha256(ss) if ss.exists() else None
        prev_sha = (prev_state[name].get('run1', {}) or {}).get('screenshot_sha256')
        verdict, draw_ops = frame_verdict(out)
        div = first_divergence(out)
        changed = sha != prev_sha
        results[name] = {
            'identity_match': ident,
            'run_rc': rc,
            'screenshot_sha256': sha,
            'sha_changed_vs_pre_fix': changed,
            'frame_verdict': verdict,
            'app_draw_ops': draw_ops,
            'next_first_divergence': div,
            'wall_s': round(time.time() - t0, 1),
        }
        print(f"{name:12s} rc={rc} sha={str(sha)[:16]} "
              f"changed={changed} verdict={str(verdict)[:28]} "
              f"draw_ops={draw_ops}")
        if div:
            print(f"             next-div: {div[:150]}")
    (ROOTA / 'root_a_fanout.json').write_text(json.dumps(results, indent=1))
    print('\nsaved', ROOTA / 'root_a_fanout.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
