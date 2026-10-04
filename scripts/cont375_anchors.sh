#!/usr/bin/env bash
# cont375_anchors.sh — determinism anchors x3 at the cont375 binary.
# Recorded anchor sha16s (EXECUTION_LEVEL_MATRIX.jsonl):
#   opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895,
#   microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/cont375/anchors
mkdir -p "$OUT"
declare -A APK=(
  [opencalc]=/home/z/my-project/upload/opencalculator_53.apk
  [chess]=/home/z/my-project/upload/chess_jwtc_298.apk
  [dooz]=/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
  [microtimer]=/home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=/home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk
)
for name in opencalc chess dooz microtimer unote; do
  st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "${APK[$name]}" --data-root "$st" > /dev/null 2>&1
  fi
  pkg=$(basename "${APK[$name]}" | sed -E 's/_[0-9]+\.apk//')
  case $name in
    opencalc) pkg=com.darkempire78.opencalculator;;
    chess) pkg=jwtc.android.chess;;
    dooz) pkg=io.github.yamin8000.dooz;;
    microtimer) pkg=dubrowgn.microtimer;;
    unote) pkg=app.varlorg.unote;;
  esac
  shas=""
  for i in 1 2 3; do
    "$B" run --package "$pkg" --data-root "$st" --max-seconds 110 \
        -o "$OUT/${name}_run$i" > /dev/null 2>&1
    s=$(sha256sum "$OUT/${name}_run$i/screenshot.png" | cut -c1-16)
    shas="$shas $s"
  done
  echo "$name:$shas"
done
