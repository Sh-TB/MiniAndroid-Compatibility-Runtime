#!/bin/bash
# CONT-11 WAVE 7 — Phase 1: dooz baseline x3 at rebuilt binary (anchor law:
# recorded CONT-10 W6 anchor d602648e8e401895 must hold zero-drift before any fix)
set -e
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont11
STORE=$OUT/store_dooz_base
APK=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
mkdir -p "$OUT"
if [ ! -d "$STORE" ]; then
  "$BIN" install "$APK" --data-root "$STORE" > "$OUT/install_dooz.log" 2>&1 || true
fi
for i in 1 2 3; do
  RUN=$OUT/dooz_base$i
  rm -rf "$RUN"; mkdir -p "$RUN"
  MINIANDROID_NODE_CENSUS=1 \
    "$BIN" run --package io.github.yamin8000.dooz --data-root "$STORE" \
    --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
    > "$RUN/run.log" 2>&1 || true
  SHA=$(sha256sum "$RUN/screenshot.png" 2>/dev/null | cut -c1-16 || echo NO_SCREENSHOT)
  OPS=$(grep -oE "APP_DRAW_OPS=[0-9]+" "$RUN/run.log" 2>/dev/null | tail -1 || echo "APP_DRAW_OPS=?")
  ERRS=$(grep -cE "EXC-UNCAUGHT|EXC-PROPAGATE" "$RUN/run.log" 2>/dev/null || echo "?")
  echo "run$i: sha16=$SHA $OPS uncaught_like=$ERRS"
done
echo "expected anchor: d602648e8e401895 (determinism anchor; white frame = DEFAULT_BACKGROUND_ONLY is the recorded honest state)"
