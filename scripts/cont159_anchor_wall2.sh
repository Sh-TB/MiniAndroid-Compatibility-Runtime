#!/bin/bash
# cont158_anchor_wall.sh — 9-anchor zero-drift wall on the 737539f1 verify pass.
# Usage: cont158_anchor_wall.sh <from> <to>
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
mkdir -p run/c159/anchors2/anchors
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
ORDER="dooz klondike unote chess telegram tower3d opencalc microtimer sudoku"
ANCHORS="dooz:d602648e klondike:31ddd4d5 unote:90a67cc1 chess:a0319686 telegram:1671f5a3 tower3d:11a38a5a opencalc:63020bc7 microtimer:bbd350b6 sudoku:be640e39"
n=0
for app in $ORDER; do
  n=$((n+1))
  [ "$n" -ge "$1" ] && [ "$n" -le "$2" ] || continue
  ms=25; [ "$app" = telegram ] && ms=60
  if [ -f "run/c159/anchors2/anchors/$app.log" ] && grep -q "^rc=" "run/c159/anchors2/anchors/$app.log" 2>/dev/null; then
    echo "SKIP $app" >> run/c159/anchors2/anchors/wall.log; continue
  fi
  timeout 120 "$B" run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$ms" -o "run/c159/anchors2/anchors/$app" > /dev/null 2> "run/c159/anchors2/anchors/$app.log"
  echo "rc=$? $app" >> run/c159/anchors2/anchors/wall.log
done
echo "ANCHOR CHUNK $1-$2 DONE" >> run/c159/anchors2/anchors/wall.log
