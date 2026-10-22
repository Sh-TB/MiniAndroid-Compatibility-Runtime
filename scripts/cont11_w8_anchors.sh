#!/usr/bin/env bash
# cont11_w8_anchors.sh — W8 regression anchors ×3 at the F-NEW-510/511 binary.
# Expected re-based faces (CONT-11 W7-REBASE record):
#   opencalc 63020bc7  chess a0319686  dooz 31ddd4d5
#   microtimer bbd350b6  unote 7481e9b4  tower3d 11a38a5a
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/w8/anchors
mkdir -p "$OUT"
declare -A APK=(
  [opencalc]=/home/z/my-project/upload/opencalculator_53.apk
  [chess]=/home/z/my-project/upload/chess_jwtc_298.apk
  [dooz]=/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
  [microtimer]=/home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=/home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk
  [tower3d]=/home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk
)
declare -A PKG=(
  [opencalc]=com.darkempire78.opencalculator
  [chess]=jwtc.android.chess
  [dooz]=io.github.yamin8000.dooz
  [microtimer]=dubrowgn.microtimer
  [unote]=app.varlorg.unote
  [tower3d]=stack.tower3d
)
for name in opencalc chess dooz microtimer unote tower3d; do
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
  echo "$name:$shas"
done
