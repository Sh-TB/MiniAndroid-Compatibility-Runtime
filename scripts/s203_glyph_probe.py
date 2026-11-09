#!/usr/bin/env python3
"""S203 — L-03 glyph-chain diagnosis on the canonical 78bdcfe9adfa801c tree.

The S202 verdict proved the tictactoe face is NOISE (uniform gray static,
center 64x64 = 4093 colors) even though:
  - the font TTF buffer is complete (F-NEW-622 one-identity law),
  - freetype binds and renders (quads carry real glyph UVs),
  - a 1024x1024 page texture uploads 75%-nonzero garbage.

This probe re-runs tictactoe with BOTH existing env-gated traces:
  MINIANDROID_W18_FT_TRACE=1   -> every FreeType/Gdx2DPixmap native call:
                                  marshalled args, native ret, kind, value
  MINIANDROID_GL_DEBUG=1       -> tex2D dumps (bytesum/nonzero), draw/attrib

and additionally a full PNG of the last frame + the W18-FT tail so we can
name the exact stage where garbage enters:
  T1 freetype render (rows/width/pitch sane?)
  T2 getBuffer -> NewDirectByteBuffer (bb box minted with bmp->buffer?)
  T3 Gdx2DPixmap newPixmap/fill/drawPixel/drawPixmap (page content writes)
  T4 tex2D upload (which pixmap goes to GL, what bytes)
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s200/runs'
STORE = RUNS / 'store_s203_glyph'
TAG = 's203_glyph_probe'


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    # fresh store, install tictactoe
    shutil.rmtree(STORE, ignore_errors=True)
    STORE.mkdir(parents=True)
    subprocess.run([str(BIN), 'install',
                    str(BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'),
                    '--data-root', str(STORE)], capture_output=True,
                   timeout=600)
    apps = STORE / 'data' / 'app'
    dpkg = [d.name for d in sorted(apps.iterdir())
            if d.is_dir() and not d.name.startswith('.')
            and not d.name.endswith('.staging')
            and (d / 'base.apk').exists()][0]

    rundir = RUNS / TAG
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{TAG}.console.log'
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
           'MINIANDROID_W18_FT_TRACE': '1',
           'MINIANDROID_GL_DEBUG': '1',
           'MINIANDROID_TEXDUMP_PREFIX': '/tmp/s203_atlas',
           'MINIANDROID_VBODUMP_PREFIX': '/tmp/s203_vbo'}
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(rundir),
           '--package', dpkg, '--frames', '40', '--frame-delay', '250']
    print('RUN', ' '.join(cmd), flush=True)
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), env=env, timeout=1800)
    log = console.read_text(errors='ignore')

    # ---- harvest the traces ----
    ft = [l for l in log.splitlines() if '[W18-FT]' in l]
    tex = [l for l in log.splitlines() if '[GLDBG] tex2D' in l]
    draws = [l for l in log.splitlines() if '[GLDBG] DRAW' in l]
    sbv = [l for l in log.splitlines() if '[GLDBG] sb_vert' in l]
    fatal = len(re.findall(r'FATAL|uncaught exception|Uncaught', log))

    out = {'tag': TAG,
           'ft_count': len(ft), 'ft_first40': ft[:40], 'ft_last40': ft[-40:],
           'tex2d': tex[:12], 'draws': draws[:16], 'sb_vert': sbv[:8],
           'fatal': fatal}
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    out['face'] = sha16(shot) if shot else None
    out['shot'] = str(shot) if shot else None

    # free-type pixmap allocation sizes (newPixmap rows) from FT trace
    np_ = [l for l in ft if 'newPixmap' in l or 'Gdx2DPixmap' in l]
    out['gdx2d_first40'] = np_[:40]
    out['gdx2d_count'] = len(np_)

    (RUNS / f'{TAG}.RESULT.json').write_text(json.dumps(out, indent=1))
    print('face:', out['face'], 'fatal:', fatal)
    print('ft_count:', len(ft), 'gdx2d_count:', len(np_))
    for l in tex[:12]:
        print(' TEX', l)
    for l in ft[:25]:
        print(' FT ', l[:180])


if __name__ == '__main__':
    main()
