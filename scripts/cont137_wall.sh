#!/usr/bin/env bash
# cont137_wall.sh — post-change zero-drift wall: 9 anchor apps, face16 compare.
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
declare -A APPS=(
 [dooz]="$CA/io.github.yamin8000.dooz_23.apk d602648e"
 [klondike]="upload/klondike_veldsoft_3.apk 31ddd4d5"
 [unote]="$CA/app.varlorg.unote_30.apk 90a67cc1"
 [chess]="upload/chess_jwtc_298.apk a0319686"
 [telegram]="upload/telegram_official.apk 20ac8cbbbb"
 [tower3d]="$CA/stack.tower3d_1.apk 11a38a5a"
 [opencalc]="upload/opencalculator_53.apk d5f3c7b5"
 [microtimer]="$CA/dubrowgn.microtimer_8.apk bbd350b6"
 [sudoku]="upload/sudoku_secuso_101.apk be640e39"
)
ORDER="dooz klondike unote chess telegram tower3d opencalc microtimer sudoku"
PASS=0; FAIL=0
for name in $ORDER; do
  apk=$(echo "${APPS[$name]}" | cut -d' ' -f1)
  anchor=$(echo "${APPS[$name]}" | cut -d' ' -f2)
  maxsec=25; [ "$name" = telegram ] && maxsec=60
  timeout 170 "$B" run "$apk" --width 1080 --height 1920 --frames 5 --max-seconds $maxsec -o "run/c137/wall/$name" > /dev/null 2> "run/c137/wall/$name.log"
  rc=$?
  face=NO_SCREENSHOT
  [ -f "run/c137/wall/$name/screenshot.png" ] && face=$(sha256sum "run/c137/wall/$name/screenshot.png" | cut -c1-16)
  if [ "${face:0:${#anchor}}" = "$anchor" ]; then echo "$name MATCH face=$face rc=$rc"; PASS=$((PASS+1)); else echo "$name DIFF face=$face anchor=$anchor rc=$rc"; FAIL=$((FAIL+1)); fi
done
echo "WALL: $PASS MATCH / $FAIL DIFF"
