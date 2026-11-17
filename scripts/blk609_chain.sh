#!/bin/bash
# Issue #609 final chain: rebuild -> fresh data root -> gameplay run -> summary
set -u
cd /home/z/my-project/miniandroid
echo "=== BUILD START $(date +%H:%M) ==="
make -j1 > make_out_b5.txt 2> make_err_b5.txt
mrc=$?
echo "=== BUILD RC=$mrc $(grep -c 'Build complete' make_out_b5.txt) ==="
[ $mrc -ne 0 ] && exit 1
sha256sum build/miniandroid | cut -c1-16
# fresh data root (one-shot guard would keep stale wrong defaults)
rm -rf runtime/data/data/data/org.blockinger.game
EV=/home/z/my-project/evidence/issue609_blockinger
rm -rf $EV/game4 && mkdir -p $EV/game4
echo "=== RUN START $(date +%H:%M) ==="
timeout 300 ./build/miniandroid run /home/z/my-project/upload/handoff_apks/org.blockinger.game_14.apk \
  -o $EV/game4 --max-seconds 240 --frames 30 --frame-delay 500 \
  --tap 816,1815@2 --tap 757,1167@4 --dump-view-tree > $EV/game4/run.log 2>&1
echo "=== RUN RC=$? ==="
echo "--- prefs ---"; cat runtime/data/data/data/org.blockinger.game/shared_prefs/org.blockinger.game_preferences.xml 2>/dev/null | head -22
echo "--- status ---"
grep -E "Status:|Message:" $EV/game4/run.log | head -2
echo "--- posts ---"; grep -c "unlockCanvasAndPost" $EV/game4/run.log
echo "--- exceptions ---"; grep -c "SYNTH-EXC" $EV/game4/run.log
grep "SYNTH-EXC" $EV/game4/run.log | head -4
python3 -c "
from PIL import Image
im = Image.open('$EV/game4/screenshot.png').convert('L')
h = im.histogram(); print('nonwhite', 1-h[255]/sum(h))
im.resize((im.width//3, im.height//3)).save('/tmp/game4_small.png')
" 2>&1
echo "=== CHAIN DONE $(date +%H:%M) ==="
