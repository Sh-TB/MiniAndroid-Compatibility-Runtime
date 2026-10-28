#!/usr/bin/env bash
# cont46_t3_wall.sh — post-R-NEW-571 zero-drift wall.
# Pins = the CONT-45 T1 recorded wall (evidence/cont45/t1_rnew570_offline.json):
#   anchors 6/6: opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 /
#                unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176
#   games   7/7: g2048 f43face0 / tetris b818a6a7 / snake_deluxe 5235683f /
#                snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f /
#                gmdice 3891679d
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
OUT=run/cont46/wall
mkdir -p $OUT

run_one() { # name apk anchor [maxsec]
  local name=$1 apk=$2 anchor=$3 ms=${4:-30}
  timeout 170 "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$ms" -o "$OUT/$name" > /dev/null 2> "$OUT/$name.log"
  local rc=$?
  local face=NO_SCREENSHOT
  [ -f "$OUT/$name/screenshot.png" ] && face=$(sha256sum "$OUT/$name/screenshot.png" | cut -c1-16)
  if [ "${face:0:${#anchor}}" = "$anchor" ]; then
    echo "$name MATCH face=$face rc=$rc"
  else
    echo "$name DIFF face=$face anchor=$anchor rc=$rc"
  fi
}

echo "== anchors =="
run_one opencalc   upload/opencalculator_53.apk                       63020bc7
run_one chess      upload/chess_jwtc_298.apk                          3f7e6707
run_one microtimer $CA/dubrowgn.microtimer_8.apk                      bbd350b6
run_one unote      $CA/app.varlorg.unote_30.apk                       7481e9b4
run_one tower3d    $CA/stack.tower3d_1.apk                            11a38a5a
run_one dooz       $CA/io.github.yamin8000.dooz_23.apk                851cc176

echo "== games =="
run_one g2048       upload/s80_games/build_2048/g2048_v1.0_vc1.apk     f43face0
run_one tetris      upload/s83_games/build_tetris/tetris_v1.0_vc1.apk  b818a6a7
run_one snake_delx  upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk 5235683f
run_one snakeneon   upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk 2617c81c
run_one ttt_delx    upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk db1d633d
run_one minicraft   upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk  e77a073f
run_one gmdice      upload/s98_games/de.duenndns.gmdice_8.apk          3891679d
