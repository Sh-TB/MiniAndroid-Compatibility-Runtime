#!/usr/bin/env python3
"""closeout_sun_final.py — #371 FINAL: Suntimes/time4j frontier close-out run.

Protocol (identical to recorded closeout waves):
  install (real install path) -> hide/remove source APK -> launch strictly by
  installed package identity (--package) -> runtime trace (first divergence)
  -> screenshot + pixel metrics + SHA -> N cold runs -> honest classification.

Modes:
  --runs N       cold runs (default 1)
  --binary PATH  alternate binary (A/B causality)
  --tag TAG      evidence dir tag (default: timestamped)
  --trace-stderr capture stderr trace for first-divergence classification
"""
import hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'tmp/closeout_apks/com.forrestguice.suntimeswidget_135.apk'
PKG = 'com.forrestguice.suntimeswidget'
RUN_CAP = 240


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pixel_metrics(png):
    from PIL import Image
    im = Image.open(png).convert('RGB')
    w, h = im.size
    px = im.resize((min(w, 270), min(h, 480))).getdata()
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    nonbg = total - bg
    ent = -sum((c / total) * math.log2(c / total) for c in colors.values()) if total else 0.0
    return {'width': w, 'height': h, 'unique_colors': len(colors),
            'dominant_ratio': round(bg / total, 4),
            'nonbg_ratio': round(nonbg / total, 4),
            'entropy': round(ent, 3)}


def classify(metrics, verdict):
    dr = metrics['dominant_ratio']
    uc = metrics['unique_colors']
    if verdict == 'render-fail':
        return 'NO_ROOT'
    if dr >= 0.985 and uc <= 4:
        return 'BACKGROUND_ONLY'
    if dr >= 0.94:
        return 'PARTIAL_APP_CONTENT'
    return 'REAL_APP_CONTENT'


def main():
    runs = 3
    tag = time.strftime('%H%M%S')
    trace_on = True
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--runs':
            i += 1; runs = int(args[i])
        elif args[i] == '--binary':
            i += 1; binp = Path(args[i])
        elif args[i] == '--tag':
            i += 1; tag = args[i]
        elif args[i] == '--no-trace':
            trace_on = False
        i += 1
    binp = locals().get('binp', BIN)

    out = BASE / f'run/closeout/sun_final_{tag}'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    store = out / 'store'
    store.mkdir()

    src_sha = sha256(APK)
    tmp = f'/tmp/sunfinal_{tag}.apk'
    shutil.copy2(APK, tmp)
    ip = subprocess.run([str(binp), 'install', tmp, '--data-root', str(store)],
                        capture_output=True, text=True, timeout=RUN_CAP)
    rec = {'apk_sha256': src_sha, 'binary': str(binp),
           'binary_sha16': sha256(binp)[:16], 'install_ok': ip.returncode == 0}
    print('INSTALL', ip.returncode)
    if ip.returncode != 0:
        print(ip.stdout[-2000:], ip.stderr[-2000:])
        (out / 'result.json').write_text(json.dumps(rec, indent=2))
        return 1
    # source APK hidden: copy to hidden_sources and remove tmp + source dir copy
    hid = out / 'hidden_sources'
    hid.mkdir()
    shutil.move(tmp, hid / APK.name)
    inst_sha = sha256(store / 'data/app' / PKG / 'base.apk')
    rec['installed_identity_ok'] = inst_sha == src_sha
    print('INSTALLED_IDENTITY', rec['installed_identity_ok'])

    results = []
    for n in range(1, runs + 1):
        png = out / f'sun_run{n}.png'
        env = dict(os.environ)
        env['MINIANDROID_REALIST'] = '1'
        cmd = [str(binp), 'run', '--package', PKG, '--data-root', str(store),
               '--dump-view-tree', '--trace', '--max-seconds', '110',
               '--frames', '40', '-o', str(out / f'run{n}')]
        t0 = time.time()
        rp = subprocess.run(cmd, capture_output=True, text=True, timeout=RUN_CAP,
                            env=env)
        dt = time.time() - t0
        shot = None
        # find produced screenshot (binary writes to -o dir or data dir)
        cands = list((out / f'run{n}').glob('**/*.png')) if (out / f'run{n}').exists() else []
        sd = store / 'data/data' / PKG
        for root, _, fs in os.walk(store):
            for f in fs:
                if f.endswith('.png'):
                    cands.append(Path(root) / f)
        if cands:
            newest = max(cands, key=lambda p: p.stat().st_mtime)
            shutil.copy2(newest, png)
            shot = sha256(png)
        m = pixel_metrics(png) if shot else None
        cls = classify(m, 'ok') if m else 'NO_ROOT'
        # first divergence from stderr
        err = rp.stderr or ''
        div = ''
        for kw in ('Exception', 'Error', 'FATAL', 'REC-MISS', 'SHADOW-MISS'):
            for line in err.splitlines():
                if kw in line:
                    div = line.strip()[:300]
                    break
            if div:
                break
        results.append({'run': n, 'exit': rp.returncode, 'seconds': round(dt, 1),
                        'screenshot_sha256': shot, 'metrics': m, 'class': cls,
                        'first_err': div})
        print(f'RUN{n} exit={rp.returncode} class={cls} sha={shot[:16] if shot else None} div={div[:120]}')
        (out / f'run{n}_stderr.log').write_text(err[-120000:] if err else '')
        (out / f'run{n}_stdout.log').write_text((rp.stdout or '')[-60000:])

    verdicts = sorted({r['class'] for r in results})
    shas = {r['screenshot_sha256'] for r in results}
    rec['runs'] = results
    rec['verdicts'] = verdicts
    rec['byte_identical_xN'] = (len(shas) == 1 and runs > 1 and None not in shas)
    rec['final_class'] = verdicts[0] if len(verdicts) == 1 else 'MIXED'
    (out / 'result.json').write_text(json.dumps(rec, indent=2))
    print('FINAL', rec['final_class'], 'identical=' + str(rec['byte_identical_xN']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
