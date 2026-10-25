#!/bin/bash
# w8_games_battery.sh — CONT-29 W1: the 7-game battery x3, byte-compare
# against the recorded CONT-28 W1 pins (zero-drift contract).
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
OUT=run/w8/games
mkdir -p "$OUT"
declare -A APKS=(
  [g2048]="upload/s80_games/build_2048/g2048_v1.0_vc1.apk"
  [tetris]="upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"
  [snake_deluxe]="upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"
  [snakeneon]="upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"
  [ttt_deluxe]="upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"
  [minicraft]="upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"
  [gmdice]="upload/canonical_apks/de.duenndns.gmdice_8.apk"
)
declare -A PKGS=(
  [g2048]=com.miniandroid.g2048 [tetris]=com.miniandroid.tetris
  [snake_deluxe]=com.miniandroid.snakedeluxe [snakeneon]=com.miniandroid.snakeneon
  [ttt_deluxe]=com.miniandroid.tictactoedeluxe [minicraft]=com.miniandroid.minicraft
  [gmdice]=de.duenndns.gmdice
)
declare -A WANT=(
  [g2048]=f43face0 [tetris]=b818a6a7 [snake_deluxe]=5235683f [snakeneon]=b669ce89
  [ttt_deluxe]=db1d633d [minicraft]=e77a073f [gmdice]=3891679d
)
for app in g2048 tetris snake_deluxe snakeneon ttt_deluxe minicraft gmdice; do
  shas=""
  rcs=""
  for i in 1 2 3; do
    o="$OUT/${app}_$i"; rm -rf "$o"; mkdir -p "$o"
    timeout 100 "$B" run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
      --max-seconds 25 -o "$o" > /dev/null 2> "$o/run.log"
    rcs="$rcs$?"
    s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
  done
  first=$(echo $shas | awk '{print $1}')
  v="DRIFT"
  case "$shas" in
    *" $first"*) ;;
  esac
  same=$(echo $shas | awk '{print ($1==$2 && $2==$3) ? "det" : "NONDET"}')
  case "$first" in
    ${WANT[$app]}*) v="MATCH($same)";;
    *) v="CHANGED($same)";;
  esac
  echo "GAME $app rc=${rcs} shas=[$shas] want=${WANT[$app]} $v"
done
