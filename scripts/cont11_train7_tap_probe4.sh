#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 4: the coroutine start chain.
# W7-T4 law: AndroidUiDispatcher = Li9; (dispatch=e(Lmr;Runnable), queue j:Lad;,
# drain l(), frameCallback Lh9; doFrame/run). Lor1;.L0 = the suspending
# pointerInputHandler launcher — probe 3 proved it NEVER enters.
# Watch: the dispatcher queue in/out + the launcher + filter lifecycle.
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc4_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Li9;|e,Li9;|l,Lh9;|run,Lor1;|L0,Lor1;|E0,Lor1;|N0,Lor1;|k0"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc4.log"
echo "exit=$?"
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc4.log" | sort | uniq -c | sort -rn
echo "=== Li9;.e (dispatch) first 10 ==="
grep "\[PMC\] Li9;.e " "$OUT/pmc4.log" | head -10
echo "=== Li9;.l (drain) first 10 ==="
grep "\[PMC\] Li9;.l " "$OUT/pmc4.log" | head -10
echo "=== Lh9; frame callback ==="
grep "\[PMC\] Lh9;.run " "$OUT/pmc4.log" | head -5
