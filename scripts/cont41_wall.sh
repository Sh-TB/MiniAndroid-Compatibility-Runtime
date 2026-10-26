#!/bin/bash
# cont38_wall.sh — anchors + games at the CONT-38 final binary (post F-NEW-543).
# Recorded pins that MUST be byte-identical:
#   opencalc 63020bc7 / chess 3f7e6707 / dooz 851cc176 / microtimer bbd350b6
#   unote 7481e9b4 / tower3d 11a38a5a
#   games: g2048 f43face0 tetris b818a6a7 snake_deluxe 5235683f snakeneon
#          2617c81c ttt_deluxe db1d633d minicraft e77a073f gmdice 3891679d
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
OUT=run/cont41/wall
mkdir -p "$OUT"
ORDER=${CONT38_SET:-"opencalc chess microtimer unote tower3d dooz"}
declare -A APKS=(
  [opencalc]=upload/opencalculator_53.apk
  [chess]=upload/chess_jwtc_298.apk
  [microtimer]="$CA/dubrowgn.microtimer_8.apk"
  [unote]="$CA/app.varlorg.unote_30.apk"
  [tower3d]="$CA/stack.tower3d_1.apk"
  [dooz]="$CA/io.github.yamin8000.dooz_23.apk"
  [g2048]="upload/s80_games/build_2048/g2048_v1.0_vc1.apk"
  [tetris]="upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"
  [snake_deluxe]="upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"
  [snakeneon]="upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"
  [ttt_deluxe]="upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"
  [minicraft]="upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"
  [gmdice]="$CA/de.duenndns.gmdice_8.apk"
)
for app in $ORDER; do
  [ -f "$OUT/$app.log" ] && grep -q "^rc=" "$OUT/$app.log" 2>/dev/null && { echo "SKIP $app"; continue; }
  ms=25; [ "$app" = dooz ] && ms=90
  timeout 300 "$B" run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$ms" -o "$OUT/$app" > /dev/null 2> "$OUT/$app.err"
  rc=$?
  sha=$(sha256sum "$OUT/$app/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "rc=$rc $app sha=$sha" | tee -a "$OUT/wall.log"
done
echo "WALL CHUNK DONE" | tee -a "$OUT/wall.log"
