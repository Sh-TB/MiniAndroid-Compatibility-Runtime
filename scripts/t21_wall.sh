#!/bin/bash
# t21_wall.sh — T21 regression wall: anchors 6/6 + games 7/7 byte-exact
# pins at HEAD c93b658d (recorded in CONT-42/43 commit messages), verifying
# the T21 diag-only engine edits (OPDUMP census + r1ran witness + anchor
# script repo-root fix) are semantically neutral.
set -u
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
CA=$BASE/upload/canonical_apks
OUT=$BASE/run/t21_wall
mkdir -p "$OUT"

run_pin() {  # name pkg apk pin
  local name=$1 pkg=$2 apk=$3 pin=$4
  local S="$OUT/store_$name" R="$OUT/run_$name"
  if [ ! -d "$S" ]; then
    "$BIN" install "$apk" --data-root "$S" > /dev/null 2>&1
  fi
  "$BIN" run --package "$pkg" --data-root "$S" \
    --width 1080 --height 1920 --frames 5 --max-seconds 90 -o "$R" \
    > "$R.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$R/screenshot.png" 2>/dev/null | cut -c1-16)
  if [[ "$sha" == "$pin"* ]]; then
    echo "PASS $name sha=$sha"
  else
    echo "FAIL $name sha=$sha pin=$pin rc=$rc"
  fi
}

run_pin dooz      io.github.yamin8000.dooz        "$CA/io.github.yamin8000.dooz_23.apk" 851cc1761a1dfcdf
run_pin opencalc  com.darkempire78.opencalculator  "$BASE/upload/opencalculator_53.apk"  63020bc7
run_pin chess     jwtc.android.chess               "$BASE/upload/chess_jwtc_298.apk"     3f7e6707
run_pin microtimer dubrowgn.microtimer            "$CA/dubrowgn.microtimer_8.apk"       bbd350b6
run_pin unote     app.varlorg.unote               "$CA/app.varlorg.unote_30.apk"        7481e9b4
run_pin tower3d   stack.tower3d                    "$CA/stack.tower3d_1.apk"             11a38a5a
