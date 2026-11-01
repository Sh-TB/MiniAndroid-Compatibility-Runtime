#!/usr/bin/env bash
# s148_anchor_wall.sh — S148 TRAIN-68 probe-neutral regression: 6-anchor zero-drift wall on
# the T61-rebate binary a892a2a097a239ea (S147 rebuild from d0899976). Pins = the standing canonical faces
# (S142/S143/S144 walls): opencalc 63020bc7 / chess 3f7e6707 / dooz 851cc176 /
# microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a.
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
OUT=run/s148_final
mkdir -p "$OUT"
declare -A APKS=(
  [opencalc]=upload/opencalculator_53.apk
  [chess]=upload/chess_jwtc_298.apk
  [dooz]=upload/canonical_apks/io.github.yamin8000.dooz_23.apk
  [microtimer]=upload/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=upload/canonical_apks/app.varlorg.unote_30.apk
  [tower3d]=upload/canonical_apks/stack.tower3d_1.apk
)
declare -A PINS=(
  [opencalc]=63020bc7334048fe
  [chess]=3f7e670759b7c6a8
  [dooz]=851cc1761a1dfcdf
  [microtimer]=bbd350b6c14fbd52
  [unote]=7481e9b468eaa376
  [tower3d]=11a38a5aeeff45a6
)
declare -A PKGS=(
  [opencalc]=com.darkempire78.opencalculator
  [chess]=jwtc.android.chess
  [dooz]=io.github.yamin8000.dooz
  [microtimer]=dubrowgn.microtimer
  [unote]=app.varlorg.unote
  [tower3d]=stack.tower3d
)
pass=0; fail=0
for app in opencalc chess dooz microtimer unote tower3d; do
  st="$OUT/store_$app"
  rm -rf "$st"; mkdir -p "$st"
  "$B" install "${APKS[$app]}" --data-root "$st" > "$OUT/${app}_install.txt" 2>&1
  o="$OUT/${app}_run"
  rm -rf "$o"; mkdir -p "$o"
  "$B" run --package "${PKGS[$app]}" --data-root "$st" --trace --max-seconds 110 --frames 25 -o "$o" > "$OUT/${app}_run.txt" 2>&1
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  if [ "$s" = "${PINS[$app]}" ]; then
    echo "$app PASS face=$s"; pass=$((pass+1))
  else
    echo "$app FAIL face=$s expected=${PINS[$app]}"; fail=$((fail+1))
  fi
done
echo "ANCHOR WALL: $pass PASS / $fail FAIL"
