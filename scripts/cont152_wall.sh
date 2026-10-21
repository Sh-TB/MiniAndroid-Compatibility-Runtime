#!/bin/bash
# cont152_wall.sh — CONT-152/153 zero-drift wall: 9 anchors at binary f6b272ea
# Fresh output dirs run/c152/wall_<app>; telegram wall param 60s (CONT-129 adjudication).
set -u
CA=upload/canonical_apks
BIN=miniandroid/build/miniandroid
declare -A APKS=(
  [dooz]="$CA/io.github.yamin8000.dooz_23.apk"
  [klondike]=upload/klondike_veldsoft_3.apk
  [unote]="$CA/app.varlorg.unote_30.apk"
  [chess]=upload/chess_jwtc_298.apk
  [telegram]=upload/telegram_official.apk
  [tower3d]="$CA/stack.tower3d_1.apk"
  [opencalc]=upload/opencalculator_53.apk
  [microtimer]="$CA/dubrowgn.microtimer_8.apk"
  [sudoku]=upload/sudoku_secuso_101.apk
)
declare -A ANCH=( [dooz]=d602648e [klondike]=31ddd4d5 [unote]=90a67cc1 [chess]=a0319686
  [telegram]=20ac8cbbbb [tower3d]=11a38a5a [opencalc]=d5f3c7b5 [microtimer]=bbd350b6 [sudoku]=be640e39 )
PASS=0; FAIL=0
for app in dooz klondike unote chess telegram tower3d opencalc microtimer sudoku; do
  ms=25; [ "$app" = telegram ] && ms=60
  out="run/c152/wall_$app"
  timeout 120 $BIN run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$ms" -o "$out" > /dev/null 2> "$out.log"
  rc=$?
  shot=$(ls "$out"/*.png 2>/dev/null | head -1)
  if [ -n "$shot" ]; then
    face=$(sha256sum "$shot" | cut -c1-16)
  else
    face=NO_SCREENSHOT
  fi
  a="${ANCH[$app]}"
  if [ "${face:0:${#a}}" = "$a" ]; then st=MATCH; PASS=$((PASS+1)); else st=DIFF; FAIL=$((FAIL+1)); fi
  echo "$app rc=$rc face=$face anchor=$a $st"
done
echo "WALL: $PASS/9 MATCH, $FAIL DIFF"
