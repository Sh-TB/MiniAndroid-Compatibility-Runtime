#!/bin/bash
# CAMPAIGN 010 P0 — baseline golden re-proof (R28/R29/R31 precondition)
set -u
cd /home/z/my-project/repo/miniandroid
OUT=/tmp/uc010
mkdir -p $OUT

sha16() { sha256sum "$1" | cut -c1-16; }
nonwhite() { python3 -c "
from PIL import Image
import sys
im = Image.open('$1').convert('RGB')
px = im.getdata()
print(sum(1 for p in px if p != (255,255,255)))
" 2>/dev/null || echo "PIL_MISSING"; }

echo "=== GMDice ==="
./build/miniandroid run -o $OUT/gmdice download/corpus/gmdice.apk > $OUT/gmdice.log 2>&1
GM_EXIT=$?
GM_IMG=$(ls $OUT/gmdice/*.png 2>/dev/null | head -1)
echo "exit=$GM_EXIT img=$GM_IMG sha16=$(sha16 $GM_IMG) nonwhite=$(nonwhite $GM_IMG)"

echo "=== Telegram ==="
./build/miniandroid run -o $OUT/tg download/exp038_telegram/Telegram.apk > $OUT/tg.log 2>&1
TG_EXIT=$?
TG_IMG=$(ls $OUT/tg/*.png 2>/dev/null | head -1)
echo "exit=$TG_EXIT img=$TG_IMG sha16=$(sha16 $TG_IMG) nonwhite=$(nonwhite $TG_IMG)"

echo "=== Dooz (attach flag ON) ==="
MINIANDROID_DISPATCH_ATTACH=1 ./build/miniandroid run -o $OUT/dooz download/corpus/dooz.apk > $OUT/dooz.log 2>&1
DZ_EXIT=$?
grep -c "UC009-ATTACH" $OUT/dooz.log | xargs echo "attach records:"
grep "ComposeView children" $OUT/dooz.log | head -2
DZ_IMG=$(ls $OUT/dooz/*.png 2>/dev/null | head -1)
echo "exit=$DZ_EXIT img=$DZ_IMG"
