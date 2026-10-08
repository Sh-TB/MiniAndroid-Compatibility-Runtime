#!/bin/bash
# cont18i_dooz_baseline.sh — CONT-18i wave baseline:
# dooz at HEAD binary a69ae4e01bb64272 (post-#382-audit A93+A62 commits).
# Verifies: (1) dooz anchor d602648e8e401895 unchanged (A93 behavior-preserving
# on dooz), (2) the F-265 arm-(c) face still reproduces ([F141-DIAG] Lnb0.S
# STRING_REF in the j slot), (3) C013-ONDRAW dispatched/ops status.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont18i
RUN=$OUT/dooz_baseline
mkdir -p "$RUN"
ST=$OUT/store_dooz
if [ ! -d "$ST" ]; then
  "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" \
    --data-root "$ST" > "$RUN/install.log" 2>&1
  echo "install rc=$?"
fi
MINIANDROID_F141_DIAG=1 \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
  --dump-view-tree --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/diag.txt"
echo "run rc=$?"
echo "=== screenshots:"
ls "$RUN" | grep -iE "png|ppm|screenshot" | head -5
SHOT=$(ls "$RUN"/*.png "$RUN"/*.ppm 2>/dev/null | head -1)
if [ -n "$SHOT" ]; then
  echo "anchor_sha16=$(sha256sum "$SHOT" | cut -c1-16)"
fi
echo "=== C013-ONDRAW (first 3):"
grep "C013-ONDRAW" "$RUN/run.log" | head -3
echo "=== C013 ops summary:"
grep -oE "C013-ONDRAW.*ops=[0-9]+" "$RUN/run.log" | sort | uniq -c | head -5
echo "=== F141-DIAG faces (first 4):"
grep "F141-DIAG" "$RUN/diag.txt" | head -4
echo "=== A93-POSTCREATE lines:"
grep -c "A93-POSTCREATE" "$RUN/run.log" "$RUN/diag.txt" 2>/dev/null | head -2
echo "=== uncaught/crash lines:"
grep -ciE "uncaught|fatal" "$RUN/run.log" || true
