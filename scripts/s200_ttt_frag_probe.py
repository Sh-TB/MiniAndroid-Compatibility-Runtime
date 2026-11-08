#!/usr/bin/env python3
"""S200 Target-B fragment-path probe — tictactoe on binary 6c808c7448850756.

The named frontier (wave record #536): the shape draw's raster output does
not land in the framebuffer. Suspects: (a) sb_frag texture-multiply vs the
shape's own v_color semantics (gdx ShapeRenderer frag = v_color, NO
texture), (b) clip/raster state.

This probe answers, with MINIANDROID_GL_DEBUG dispatch traces:
  1. at shape draws: sb_vert proj00 (is the engine matrix the shape's own?)
  2. sb_frag v_color / uv / bound texture id at shape draws
  3. whether board pixels land (frame face vs the S199 glyph pin)
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
APK = BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
OUT = BASE / 'evidence/s200'
RUNS = OUT / 'runs'
RUNS.mkdir(parents=True, exist_ok=True)

tag = sys.argv[1] if len(sys.argv) > 1 else 'ttt_f625_fragprobe'
FRAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 40
DELAY = int(sys.argv[3]) if len(sys.argv) > 3 else 250
# tap schedule: cell centers on the 1080x1920 GL surface (same as s199).
TAPS = [
    (6,   270, 560),
    (12,  810, 560),
    (18,  270, 960),
    (24,  810, 960),
    (30,  270, 1360),
]

store = RUNS / f'store_{tag}'
store.mkdir(parents=True, exist_ok=True)
r = subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
                   capture_output=True, timeout=300)
apps = store / 'data' / 'app'
dpkg = None
if apps.exists():
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith('.')
          and not d.name.endswith('.staging')
          and (d / 'base.apk').exists()]
    dpkg = ds[0] if ds else None
print('dpkg:', dpkg, 'install rc:', r.returncode)

rundir = RUNS / tag
shutil.rmtree(rundir, ignore_errors=True)
console = RUNS / f'{tag}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', str(FRAMES),
       '--frame-delay', str(DELAY), '--trace']
for (fr, x, y) in TAPS:
    cmd += ['--tap', f'{x},{y}@{fr}']

env_cmd = ' '.join(cmd)
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=FRAMES * DELAY // 1000 + 300,
                   env={'MINIANDROID_GL_DEBUG': '1',
                        'PATH': '/usr/bin:/bin', 'HOME': '/home/z'})
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

res = {
    'binary_sha16': BIN_SHA, 'tag': tag, 'wall_s': wall,
    'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
    'gldbg_vap_raw': re.findall(r'\[GLDBG\] vap RAW.*', log)[:8],
    'gldbg_attrib': re.findall(r'\[GLDBG\] attrib idx.*', log)[:6],
    'gldbg_mat4': re.findall(r'\[GLDBG\] mat4 .*', log)[:6],
    'gldbg_draw': re.findall(r'\[GLDBG\] DRAW .*', log)[:12],
    'gldbg_sbvert': re.findall(r'\[GLDBG\] sb_vert.*', log)[:10],
    'gldbg_sbfrag': re.findall(r'\[GLDBG\] sb_frag.*', log)[:10],
    'gldbg_tex2d': re.findall(r'\[GLDBG\] tex2D .*', log)[:6],
    'gldbg_attribloc': re.findall(r'\[GLDBG\] attrib-loc.*', log)[:10],
}
shot = rundir / 'final_frame.png'
if not shot.exists():
    cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
    shot = cands[-1] if cands else None
if shot and shot.exists():
    face = OUT / f'face_{tag}.png'
    shutil.copy(shot, face)
    res['face'] = str(face)
    res['face_sha16'] = hashlib.sha256(face.read_bytes()).hexdigest()[:16]
    # honest gate: center 64x64 patch color census
    try:
        from PIL import Image
        im = Image.open(face).convert('RGB')
        w, h = im.size
        cx, cy = w // 2, h // 2
        px = im.crop((cx - 32, cy - 32, cx + 32, cy + 32))
        colors = px.getcolors(64 * 64)
        colors.sort(reverse=True)
        res['center_top_colors'] = [(c, f'#{r:02x}{g:02x}{b:02x}')
                                    for c, (r, g, b) in colors[:6]]
        res['center_unique'] = len(colors)
    except Exception as e:
        res['center_err'] = str(e)

print(json.dumps(res, indent=1))
(OUT / f'{tag}.RESULT.json').write_text(json.dumps(res, indent=1))
