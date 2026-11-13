#!/usr/bin/env python3
"""S232 — independent F-SQLQB verification on the MAIN line (#592 reconciliation).

Runs OpenSudoku (org.moire.opensudoku, F-Droid 4.11.3, sha256
ac4c6c8d0bc9058c1cc8d8f4570dc51977b3bc51577a82a12b94e6ec7714b9f0) on the
post-SQLQB binary and records: the SQLiteQueryBuilder query row, the
SimpleCursorAdapter materialization (Easy/Medium/Hard), the EXP092 render
walk, the final face, and honest uncaught counters.

Output: evidence/s232/S232_SQLQB_OPENSUDOKU.json + runs/s232_opensudoku/.
"""
import hashlib, json, re, shutil, subprocess, time, os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # R11 repo-root discovery
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s232'
RUN = OUT / 'runs/s232_opensudoku'
STORE = BASE / 'evidence/s207/runs/store_s232_opensudoku'
APK = BASE / 'upload/opensudoku_v4113.apk'


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    STORE.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(STORE)],
                   capture_output=True, timeout=300)
    apps = STORE / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    shutil.rmtree(RUN, ignore_errors=True)
    console = OUT / 's232_opensudoku.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUN),
           '--package', dpkg, '--frames', '10', '--frame-delay', '200']
    env = os.environ.copy()
    env['MINIANDROID_SQLITE_QB_TRACE'] = '1'
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=900, env=env)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = RUN / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None

    qb = re.findall(r'\[SQLITE-QB\][^\n]*', log)
    rawq = re.findall(r'\[SQLITE-SHADOW\] rawQuery[^\n]*', log)
    ca = re.findall(r'\[F-SQLQB-CURSORADAPTER\][^\n]*', log)
    s191 = re.findall(r'\[S191-ADAPTER\][^\n]*', log)
    walk = re.findall(r'\[EXP092-RENDER\][^\n]*', log)
    uncaught = len(re.findall(r'uncaught at caller', log))

    # face content census
    colors = None
    if shot.exists():
        try:
            from PIL import Image
            import collections
            img = Image.open(shot).convert('RGB')
            colors = collections.Counter(img.getdata())
        except Exception:
            pass

    rec = {
        'binary_sha16': sha16(BIN),
        'apk': 'org.moire.opensudoku 4.11.3 (F-Droid 20261008)',
        'apk_sha256': hashlib.sha256(APK.read_bytes()).hexdigest(),
        'wall_s': wall,
        'final_face_sha16': face,
        'uncaught_escapes': uncaught,
        'sqlite_qb_rows': qb[:4],
        'rawquery_rows': rawq[:4],
        'cursoradapter_rows': ca[:10],
        'adapter_rematerialize': s191[:3],
        'render_walk_nodes': len(walk),
        'render_walk_head': walk[:8],
        'distinct_colors': len(colors) if colors is not None else None,
    }
    (OUT / 'S232_SQLQB_OPENSUDOKU.json').write_text(json.dumps(rec, indent=1))
    for k in ('binary_sha16', 'apk_sha256', 'wall_s', 'final_face_sha16',
              'uncaught_escapes', 'distinct_colors', 'render_walk_nodes'):
        print(f"{k}: {rec[k]}")
    for r in qb[:3]:
        print('QB:', r)
    for r in ca[:8]:
        print('CA:', r)


if __name__ == '__main__':
    main()
