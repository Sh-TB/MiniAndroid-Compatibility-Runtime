#!/bin/bash
# cont28_dooz_300s_probe.sh — discriminator: is the dooz board (a) never placed
# (isPlaced gate -> chrome-only ops even with huge budget) or (b) walk too slow
# (frame never completes within budget)?
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont28
RUN=$OUT/dooz_300s
mkdir -p "$RUN"
ST=$OUT/store_dooz300
if [ ! -d "$ST" ]; then
  "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" \
    --data-root "$ST" > "$RUN/install.log" 2>&1
  echo "install rc=$?"
fi
MINIANDROID_COMPOSE_MEASURE_TRACE=1 \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
  --max-seconds 300 --frames 12 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/diag.txt"
echo "run rc=$?"
echo "=== per-frame op counts (last complete frame wins):"
grep -oE "C013-ONDRAW.*ops=[0-9]+" "$RUN/diag.txt" | tail -5
echo "=== F298 keep / halt count:"
grep -c "F298-KEEP" "$RUN/diag.txt"
echo "=== last frame diff:"
ls "$RUN"/frames/ | tail -3
echo "=== screenshot sha16 + colors:"
python3 - <<'EOF'
from PIL import Image
import collections, hashlib, glob, os
runs = sorted(glob.glob('/home/z/my-project/run/cont28/dooz_300s/frames/frame_*.png'),
              key=lambda p: int(''.join(c for c in os.path.basename(p) if c.isdigit())))
for p in runs[-3:]:
    im = Image.open(p).convert('RGB')
    cnt = collections.Counter(im.getdata())
    dom = cnt.most_common(1)[0][1]
    print(os.path.basename(p), 'colors=', len(cnt), 'dom%=', round(100*dom/(im.width*im.height),1),
          'sha16=', hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])
im = Image.open('/home/z/my-project/run/cont28/dooz_300s/screenshot.png').convert('RGB')
cnt = collections.Counter(im.getdata())
print('FINAL screenshot colors=', len(cnt), 'sha16=', hashlib.sha256(open('/home/z/my-project/run/cont28/dooz_300s/screenshot.png','rb').read()).hexdigest()[:16])
EOF
