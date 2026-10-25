#!/bin/bash
# cont32_baseline.sh — CONT-32 PRE/POST measurement battery.
# Usage: cont32_baseline.sh [pre|post]
# PRE : dooz 90s anchor + PERF opcode census + telegram 60s state
# POST: same rows after the CowStr structural lever lands (A/B pair)
set -u
ROOT=/home/z/my-project
BIN=$ROOT/miniandroid/build/miniandroid
CA=$ROOT/upload/canonical_apks
TAG=${1:-pre}
OUT=$ROOT/run/cont32
mkdir -p "$OUT"

echo "=== [$TAG] dooz 90s anchor (expect 851cc176 at PRE) ==="
rm -rf "$OUT/dooz_$TAG"; mkdir -p "$OUT/dooz_$TAG"
if [ ! -d "$OUT/store_dooz" ]; then
  "$BIN" install "$CA/io.github.yamin8000.dooz_23.apk" --data-root "$OUT/store_dooz" > "$OUT/dooz_install.log" 2>&1
  echo "install rc=$?"
fi
"$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --max-seconds 90 --frames 6 -o "$OUT/dooz_$TAG" > "$OUT/dooz_${TAG}.log" 2> "$OUT/dooz_${TAG}.diag"
echo "rc=$?"
python3 - <<EOF
from PIL import Image
import collections, hashlib, glob, os
runs = sorted(glob.glob('$OUT/dooz_$TAG/frames/frame_*.png'),
              key=lambda p: int(''.join(c for c in os.path.basename(p) if c.isdigit())))
for p in runs[-2:]:
    im = Image.open(p).convert('RGB')
    cnt = collections.Counter(im.getdata())
    dom = cnt.most_common(1)[0][1]
    print(os.path.basename(p), 'colors=', len(cnt), 'sha16=', hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])
p = '$OUT/dooz_$TAG/screenshot.png'
if os.path.exists(p):
    im = Image.open(p).convert('RGB')
    cnt = collections.Counter(im.getdata())
    print('screenshot colors=', len(cnt), 'sha16=', hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])
EOF
grep -c "F298-KEEP" "$OUT/dooz_${TAG}.diag" 2>/dev/null | sed 's/^/F298-KEEP=/'
grep -oE "APP_DRAW_OPS=[0-9]+" "$OUT/dooz_${TAG}.log" 2>/dev/null | tail -1
grep -c "uncaught" "$OUT/dooz_${TAG}.log" 2>/dev/null | sed 's/^/uncaught-lines=/'

echo ""
echo "=== [$TAG] dooz PERF opcode census (90s) ==="
rm -rf "$OUT/dooz_perf_$TAG"; mkdir -p "$OUT/dooz_perf_$TAG"
MINIANDROID_PERF_PHASES=1 "$BIN" run --package io.github.yamin8000.dooz \
  --data-root "$OUT/store_dooz" --max-seconds 90 --frames 6 -o "$OUT/dooz_perf_$TAG" \
  > "$OUT/dooz_perf_${TAG}.log" 2> "$OUT/dooz_perf_${TAG}.perf"
grep -A14 "PERF-OPS" "$OUT/dooz_perf_${TAG}.perf" | head -16
grep -E "PERF-PHASE.*(fetch_exec|insn_pre|insn_post|resolve_field|bridge)" "$OUT/dooz_perf_${TAG}.perf" | head -8

echo ""
echo "=== [$TAG] telegram 60s state ==="
rm -rf "$OUT/tg_$TAG"; mkdir -p "$OUT/tg_$TAG"
"$BIN" run "$ROOT/upload/telegram_official.apk" --width 1080 --height 1920 --frames 5 \
  --max-seconds 60 -o "$OUT/tg_$TAG" > "$OUT/tg_${TAG}.log" 2> "$OUT/tg_${TAG}.diag"
echo "rc=$?"
python3 - <<EOF
from PIL import Image
import collections, hashlib, os
p = '$OUT/tg_$TAG/screenshot.png'
if os.path.exists(p):
    im = Image.open(p).convert('RGB')
    cnt = collections.Counter(im.getdata())
    dom = cnt.most_common(1)[0][1]
    print('screenshot colors=', len(cnt), 'dom%=', round(100*dom/(im.width*im.height),1),
          'sha16=', hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])
else:
    print('NO screenshot')
EOF
echo "uncaught count: $(grep -c 'EXC-PROPAGATE.*uncaught' "$OUT/tg_${TAG}.log" 2>/dev/null || echo 0)"
echo "UPP/GATEA faces: $(grep -c 'GATEA-NATIVE' "$OUT/tg_${TAG}.log" 2>/dev/null || echo 0)"
grep -E "\[SYNTH-EXC\]" "$OUT/tg_${TAG}.log" 2>/dev/null | tail -4
