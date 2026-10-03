#!/usr/bin/env python3
"""CONT-ROOT-C — Fragment-recreation fan-out: install + run two UNRELATED
Fragment-based apps (stardroid, suntimeswidget) on the patched binary with
the canonical installed-identity protocol, then record their first
divergence / frame verdict. No package-specific code; generic pipeline."""
import hashlib, json, subprocess, os, shutil, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
WORK = BASE / 'run/diff366'
HID = WORK / 'hidden_sources'
ROOTC = BASE / 'evidence/diff366/root_c'
RUN_CAP = 170

APPS = [
    ('stardroid', 'com.google.android.stardroid',
     HID / 'com.google.android.stardroid_1751.apk'),
    ('suntimes', 'com.forrestguice.suntimeswidget',
     HID / 'com.forrestguice.suntimeswidget_135.apk'),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ROOTC.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, pkg, src in APPS:
        store = WORK / 'stores' / f'store_{name}'
        if store.exists():
            shutil.rmtree(store)
        store.mkdir(parents=True)
        tmp = f'/tmp/rootc_{name}.apk'
        shutil.copy2(src, tmp)
        src_sha = sha256(tmp)
        ip = subprocess.run([str(BIN), 'install', tmp, '--data-root', str(store)],
                            capture_output=True, text=True, timeout=RUN_CAP)
        if ip.returncode != 0:
            print(f'{name}: INSTALL FAIL'); results[name] = {'install': 'FAIL'}; continue
        inst = store / 'data/app' / pkg / 'base.apk'
        inst_sha = sha256(inst)
        pa = subprocess.run([str(BIN), 'pkgaudit', '--package', pkg,
                             '--data-root', str(store)],
                            capture_output=True, text=True, timeout=120)
        try:
            live = json.loads(pa.stdout).get('liveBaseApkSha256')
        except Exception:
            live = None
        ident = (src_sha == inst_sha == live)
        out = ROOTC / f'{name}_{pkg}'
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
        t0 = time.time()
        with open(out / 'run.log', 'w') as f:
            try:
                rp = subprocess.run([str(BIN), 'run', '--package', pkg,
                                     '--data-root', str(store),
                                     '--dump-view-tree', '--trace',
                                     '--max-seconds', '110', '-o', str(out)],
                                    stdout=f, stderr=subprocess.STDOUT,
                                    env=env, timeout=RUN_CAP)
                rc = rp.returncode
            except subprocess.TimeoutExpired:
                rc = 'TIMEOUT'
        ss = out / 'screenshot.png'
        sha = sha256(ss) if ss.exists() else None
        div = None
        for line in (out / 'run.log').read_text(errors='replace').splitlines():
            if '[THROWABLE-MSG]' in line or '[EXC-PROPAGATE]' in line:
                div = line[:220]; break
        verdict = None
        ts = out / 'trace_summary.json'
        if ts.exists():
            try:
                fa = json.load(open(ts)).get('frame_analysis') or {}
                verdict = fa.get('verdict')
            except Exception:
                pass
        results[name] = {
            'identity': {'source_sha256': src_sha, 'installed_sha256': inst_sha,
                         'pkgaudit_live_sha256': live, 'match': ident},
            'run_rc': rc, 'screenshot_sha256': sha,
            'frame_verdict': verdict, 'next_first_divergence': div,
            'wall_s': round(time.time() - t0, 1),
        }
        print(f"{name}: ident={ident} rc={rc} sha={str(sha)[:16]} "
              f"verdict={str(verdict)[:26]}")
        if div:
            print(f"  div: {div[:160]}")
        os.remove(tmp)
    (ROOTC / 'root_c_fanout.json').write_text(json.dumps(results, indent=1))
    print('saved', ROOTC / 'root_c_fanout.json')


if __name__ == '__main__':
    main()
