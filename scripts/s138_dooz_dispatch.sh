#!/usr/bin/env bash
# S138 dooz next station: dump the FULL R8 call graph of
# AndroidComposeView.dispatchTouchEvent (Lt4;) via the S136c INVOKE-SITES
# entry dump -> the exact pointer-input chain (R8 names) for the hit-test
# watchlist (post-PMC-refutation station: filter constructed, never entered).
set -u
cd /home/z/my-project
OUT=run/s138_dooz_dispatch
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_INVOKE_SITES="Lt4;|dispatchTouchEvent"
export MINIANDROID_THROW_TRACE=1
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 --max-seconds 520 \
  --tap 765,1830@5 --dump-view-tree -o "$OUT" 2>"$OUT/dispatch.log"
echo "exit=$?"
rg -n 'INVOKE-SITE' "$OUT/dispatch.log" 2>/dev/null | sed -n 1,80p
echo "total=$(rg -c 'INVOKE-SITE' "$OUT/dispatch.log" 2>/dev/null || echo 0)"
