#!/usr/bin/env python3
"""S232 — the W23 (0,0) EXIT-REASON census on the MAIN line.

Integrates the Coder-4 W23 census probe (#591, w23_probe_only.diff —
applied verbatim, six-pin gate ALL HOLD byte-exact on the probe binary
0672ecac127664fa, default-neutrality proven) and runs the dooz post-nav
census scenario (the S208/S210 recipe: tap New game (875,1823)@8,
frames=12, delay=100) with MINIANDROID_W23_EXIT0=1.

Expected from the Coder-4 line (528efe5a): 70 census rows, unified
signature Lsr;.run pc 0xfe, mid-frame catch-handler breaks, no pending
exception, 0/70 off-end. Main may differ — honest measurement.

Output: evidence/s232/S232_W23_CENSUS.json + runs/s232_dooz_census/ +
console log. Default-neutrality: the gate JSON at evidence/s207/runs/
S207_GATE.json (binary_sha16 0672ecac127664fa) is the companion record.
"""
import hashlib, json, re, shutil, subprocess, time, os
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s232'
RUN = OUT / 'runs/s232_dooz_census'
STORE = BASE / 'evidence/s207/runs/store_s210_dooz_s36'
APK = BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'


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
    console = OUT / 's232_dooz_census.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUN),
           '--package', dpkg, '--frames', '12', '--frame-delay', '100',
           '--tap', '875,1823@8']
    env = os.environ.copy()
    env['MINIANDROID_W23_EXIT0'] = '1'
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=900, env=env)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = RUN / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None

    rows = re.findall(r'\[W23-EXIT0\] (\S+)\.(\S+) pc=(0x[0-9a-f]+) '
                      r'of (0x[0-9a-f]+) next_op=(0x[0-9a-f]+) '
                      r'instr=(\S+) pexc_type=(\d+) unwind=(\d)', log)
    census = []
    for cls, meth, pc, size, op, seq, pexc, unwind in rows:
        census.append({
            'class': cls, 'method': meth.rstrip(':'),
            'pc': int(pc, 16), 'bytecode_size': int(size, 16),
            'next_op': int(op, 16), 'instr_seq': int(seq),
            'pexc_type': int(pexc), 'unwind': int(unwind),
        })

    # signature clustering — the W23 law answer shape
    from collections import Counter
    sig = Counter((r['class'], r['method'], r['pc']) for r in census)
    off_end = sum(1 for r in census if r['pc'] >= r['bytecode_size'])
    with_pexc = sum(1 for r in census if r['pexc_type'] != 0)
    with_unwind = sum(1 for r in census if r['unwind'] != 0)

    uncaught = len(re.findall(r'uncaught at caller', log))
    rec = {
        'binary_sha16': sha16(BIN),
        'apk_sha16': sha16(APK),
        'wall_s': wall,
        'final_face_sha16': face,
        'uncaught_escapes': uncaught,
        'census_rows': len(census),
        'off_end_rows': off_end,
        'rows_with_pending_exception': with_pexc,
        'rows_with_unwind': with_unwind,
        'signature_clusters': [
            {'class': k[0], 'method': k[1], 'pc': k[2], 'count': v}
            for k, v in sig.most_common(10)
        ],
        'coder4_line_reference': {
            'tree': '528efe5a', 'rows': 70,
            'signature': 'Lsr;.run pc 0xfe',
            'shape': 'mid-frame catch-handler breaks, no pending exception, 0/70 off-end',
        },
        'probe': 'w23_probe_only.diff sha256 f35901eba4c247cb1a027fff4b94ae13db956110bbbf692b444ea3a8b1031668 (verbatim, #591 comment 6859402179)',
        'gate': 'evidence/s207/runs/S207_GATE.json binary 0672ecac127664fa six-pin ALL HOLD',
    }
    (OUT / 'S232_W23_CENSUS.json').write_text(json.dumps(rec, indent=1))
    print(json.dumps({k: v for k, v in rec.items()
                      if k != 'signature_clusters'}, indent=1))
    for c in rec['signature_clusters'][:6]:
        print('  cluster:', c)


if __name__ == '__main__':
    main()
