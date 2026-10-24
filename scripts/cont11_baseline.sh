#!/bin/bash
# cont11_baseline.sh — CONT-11 W7: reproduce the CONT-10 lineage honestly.
# dooz x3 anchor + the other 4 anchors at the freshly rebuilt binary.
# Expected (recorded): binary aed46450c103f2ea; anchors dooz d602648e8e401895,
# chess b5a7a35d5fe0564b, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8,
# opencalc a976d2f9fb675cb3 (CONT-10 changed anchor, flagged honestly).
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/w7/anchors
mkdir -p "$OUT"
echo "== binary sha16 =="
sha256sum "$B" | cut -c1-16

declare -A APK=(
  [opencalc]=/home/z/my-project/upload/opencalculator_53.apk
  [chess]=/home/z/my-project/upload/chess_jwtc_298.apk
  [dooz]=/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
  [microtimer]=/home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=/home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk
)
declare -A PKG=(
  [opencalc]=com.darkempire78.opencalculator
  [chess]=jwtc.android.chess
  [dooz]=io.github.yamin8000.dooz
  [microtimer]=dubrowgn.microtimer
  [unote]=app.varlorg.unote
)
for name in opencalc chess dooz microtimer unote; do
  st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "${APK[$name]}" --data-root "$st" > /dev/null 2>&1
  fi
  shas=""
  for i in 1 2 3; do
    o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    "$B" run --package "${PKG[$name]}" --data-root "$st" --trace --max-seconds 90 --frames 40 -o "$o" > /dev/null 2>&1 || true
    s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
  done
  echo "ANCHOR $name:$shas"
done
