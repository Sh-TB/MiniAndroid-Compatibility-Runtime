#!/bin/bash
# cont32_dooz_gate.sh — the CowStr-neutrality gate: dooz 90s x3 (851cc176).
set -u
ROOT=/home/z/my-project
BIN=$ROOT/miniandroid/build/miniandroid
OUT=$ROOT/run/cont32/dooz_gate
mkdir -p "$OUT"
ST=$OUT/store_dooz
if [ ! -d "$ST" ]; then
  "$BIN" install "$ROOT/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" \
    --data-root "$ST" > "$OUT/install.log" 2>&1
  echo "install rc=$?"
fi
for i in 1 2 3; do
  O="$OUT/r$i"; rm -rf "$O"; mkdir -p "$O"
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --max-seconds 90 --frames 40 -o "$O" > "$O/run.log" 2> "$O/diag.txt"
  rc=$?
  sha=$(sha256sum "$O/screenshot.png" 2>/dev/null | cut -c1-16)
  verdict="DRIFT"; [ "$sha" = "851cc176" ] && verdict="MATCH"
  echo "DOOZ r$i rc=$rc sha=$sha want=851cc176 $verdict"
done
