#!/usr/bin/env bash
# s66_tictactoe_package.sh — §4/§13: TicTacToe visual evidence package.
#
# Builds the golden fixture once (deterministic build), performs THREE
# independent engine runs (--click-count 9, the R-NEW-358 interaction law),
# and for each run records the FULL frames required by the S66 brief:
#   initial_full.png  (frame_000 — before any input)
#   mid_full.png      (frame_003 — after 3 real clicks)
#   win_full.png      (frame_007 — X WINS state)
#   final_full.png    (frame_009 — frozen board, 4X+3O)
#   diff.png          (initial vs win, amplified)
#   metrics.json      (independent pixel re-read: SHA/dims/nonwhite/bbox)
# Cross-run determinism table printed at the end.
set -euo pipefail
REPO=/home/z/my-project
PKG="$REPO/docs/evidence/visual_forensics/tictactoe"
BIN="$REPO/miniandroid/build/miniandroid"
FIXTURE="$REPO/miniandroid/tests/fixtures/tictactoe_golden"
APK=/tmp/s66_tictactoe.apk

bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > /tmp/s66_ttt_build.log 2>&1
APK_SHA=$(grep '^SHA256:' /tmp/s66_ttt_build.log | cut -d' ' -f2)
echo "APK SHA256 = $APK_SHA"

for RUN in 1 2 3; do
  OUT="$PKG/run$RUN"
  rm -rf "$OUT"; mkdir -p "$OUT"
  echo "── RUN $RUN ──"
  timeout 400 "$BIN" run "$APK" -o "$OUT/engine" --click-count 9 > "$OUT/engine_stdout.log" 2>&1
  rc=$?
  echo "engine rc=$rc"
  # Full frames (uncropped, straight from the engine frame capture)
  cp "$OUT/engine/frames/frame_000.png" "$OUT/initial_full.png"
  cp "$OUT/engine/frames/frame_003.png" "$OUT/mid_full.png"
  cp "$OUT/engine/frames/frame_007.png" "$OUT/win_full.png"
  cp "$OUT/engine/frames/frame_009.png" "$OUT/final_full.png"
  # Independent diff (initial vs win)
  python3 "$REPO/scripts/s66_png_metrics.py" diff \
      "$OUT/initial_full.png" "$OUT/win_full.png" "$OUT/diff.png" > "$OUT/diff_metrics.json"
  # Metrics for each full frame (independent PIL re-read)
  python3 - "$OUT" "$APK_SHA" "$RUN" <<'PY'
import hashlib, json, os, subprocess, sys
out, apk_sha, run = sys.argv[1], sys.argv[2], sys.argv[3]
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()
man_path = os.path.join(out, 'engine', 'frames', 'manifest.json')
man = json.load(open(man_path)) if os.path.exists(man_path) else {}
metrics = {
    'apk_sha256': apk_sha,
    'run': int(run),
    'engine_cmd': 'miniandroid run <apk> -o <out>/engine --click-count 9',
    'engine_head': subprocess.run(['git', '-C', '/home/z/my-project', 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True).stdout.strip(),
    'clicks_dispatched': man.get('clicks_dispatched'),
    'frames': {},
    'visible_texts': {i: man['frames'][i].get('visible_texts') for i in range(len(man.get('frames', [])))},
}
for name in ('initial_full', 'mid_full', 'win_full', 'final_full'):
    p = os.path.join(out, f'{name}.png')
    m = json.loads(subprocess.run(
        ['python3', '/home/z/my-project/scripts/s66_png_metrics.py', 'metrics', p],
        capture_output=True, text=True).stdout)
    m['source_frame'] = name.replace('_full', '')
    m['source_framebuffer'] = 'engine framebuffer_ (RGBA, 0xFF-init) -> PNGWriter(libpng) -> ' + name
    metrics['frames'][name] = m
json.dump(metrics, open(os.path.join(out, 'metrics.json'), 'w'), indent=2)
print('metrics.json written')
PY
done

echo "── DETERMINISM TABLE ──"
for RUN in 1 2 3; do
  for F in initial_full mid_full win_full final_full; do
    S=$(sha256sum "$PKG/run$RUN/$F.png" | cut -c1-16)
    echo "run$RUN $F $S"
  done
done
