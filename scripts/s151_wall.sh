#!/usr/bin/env bash
# s151_wall.sh — S151 wave: anchor wall at the fresh my-project build.
# Same standing pins as S148/S149-TRUE (opencalc 63020bc7 / chess 3f7e6707 /
# dooz 851cc176 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a +
# g2048 f43face08 / tetris b818a6a7 / snakedeluxe 5235683f / minicraft e77a073f /
# gmem 4876e47d / snakeneon b669ce89 / sqlnotes 748bb6cf). x3 byte-exact each.
# Usage: s151_wall.sh <name> ...   (default: all 13)
BASE=/home/z/my-project
B=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/s151_wall
APKB=$BASE/upload
mkdir -p "$OUT"
cd "$BASE/miniandroid"

declare -A APK=(
  [opencalc]=$APKB/opencalculator_53.apk
  [chess]=$APKB/chess_jwtc_298.apk
  [dooz]=$APKB/canonical_apks/io.github.yamin8000.dooz_23.apk
  [microtimer]=$APKB/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=$APKB/canonical_apks/app.varlorg.unote_30.apk
  [tower3d]=$APKB/canonical_apks/stack.tower3d_1.apk
  [g2048]=$APKB/s80_games/build_2048/g2048_v1.0_vc1.apk
  [tetris]=$APKB/s80_games/build_tetris/tetris_v1.0_vc1.apk
  [snakedeluxe]=$APKB/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk
  [minicraft]=$APKB/s86_games/build_minicraft/minicraft_v1.0_vc1.apk
  [gmem]=$APKB/s80_games/build_mem/gmem_v1.0_vc1.apk
  [snakeneon]=$APKB/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk
  [sqlnotes]=$APKB/s142_sqlnotes/build/sqlnotes_v1.0_vc1.apk
)
declare -A PKG=(
  [opencalc]=com.darkempire78.opencalculator
  [chess]=jwtc.android.chess
  [dooz]=io.github.yamin8000.dooz
  [microtimer]=dubrowgn.microtimer
  [unote]=app.varlorg.unote
  [tower3d]=stack.tower3d
  [g2048]=com.miniandroid.g2048
  [tetris]=com.miniandroid.tetris
  [snakedeluxe]=com.miniandroid.snakedeluxe
  [minicraft]=com.miniandroid.minicraft
  [gmem]=com.miniandroid.gmem
  [snakeneon]=com.miniandroid.snakeneon
  [sqlnotes]=com.miniandroid.sqlnotes
)
declare -A PIN=(
  [opencalc]=63020bc7334048fe
  [chess]=3f7e670759b7c6a8
  [dooz]=851cc1761a1dfcdf
  [microtimer]=bbd350b6c14fbd52
  [unote]=7481e9b468eaa376
  [tower3d]=11a38a5aeeff45a6
  [g2048]=f43face08299ffc6
  [tetris]=b818a6a7016bea8e
  [snakedeluxe]=5235683fc7b1f04b
  [minicraft]=e77a073f733255eb
  [gmem]=4876e47d26910839
  [snakeneon]=b669ce89365f8bbe
  [sqlnotes]=748bb6cf756e7413
)

names=("$@"); [ ${#names[@]} -eq 0 ] && names=(opencalc chess dooz microtimer unote tower3d g2048 tetris snakedeluxe minicraft gmem snakeneon sqlnotes)
pass=0; fail=0
for name in "${names[@]}"; do
  st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "${APK[$name]}" --data-root "$st" > /dev/null 2>&1
  fi
  shas=""; ok=1
  for i in 1 2 3; do
    o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    timeout 110 "$B" run --package "${PKG[$name]}" --data-root "$st" --trace --max-seconds 90 --frames 40 -o "$o" > /dev/null 2>&1 || true
    s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    [ "$s" == "${PIN[$name]}" ] || ok=0
    shas="$shas $s"
  done
  if [ $ok -eq 1 ]; then pass=$((pass+1)); v=PASS; else fail=$((fail+1)); v="FAIL(pin=${PIN[$name]})"; fi
  echo "$name:$v$shas"
done
echo "WALL: $pass PASS / $fail FAIL"
