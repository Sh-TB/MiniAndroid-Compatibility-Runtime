#!/bin/bash
# cont18_anchors.sh — CONT-18 T-01 (PHASE 0): 6 anchors x3 + Telegram x3.
# Usage: bash scripts/cont18_anchors.sh [part1|part2|telegram]
#   part1     = dooz microtimer unote      (x3 each)
#   part2     = gmdice opencalc chess      (x3 each)
#   telegram  = org.telegram.messenger.web (x3)
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont18/anchors
CA=$BASE/upload/canonical_apks
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  part: ${1:-ALL}"

run3() { # run3 <pkg> <apkpath> <want-sha|none>
  local pkg="$1" apk="$2" want="${3:-none}"
  local store="$OUT/store_$pkg"
  [ -d "$store" ] || "$BIN" install "$apk" --data-root "$store" > /dev/null 2>&1
  for i in 1 2 3; do
    local o="$OUT/${pkg}_$i"; rm -rf "$o"; mkdir -p "$o"
    timeout 300 "$BIN" run --package "$pkg" --data-root "$store" --trace \
      --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
    local sha
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    if [ "$sha" = "$want" ]; then
      echo "ANCHOR $pkg run$i sha=$sha MATCH"
    else
      echo "ANCHOR $pkg run$i sha=$sha RECORDED=$want DRIFT"
    fi
  done
}

case "${1:-ALL}" in
  part1|ALL)
    run3 io.github.yamin8000.dooz "$CA/dooz_23_toplevel.apk" d602648e8e401895
    run3 dubrowgn.microtimer     "$CA/dubrowgn.microtimer_8.apk" da73010a37dd0189
    run3 app.varlorg.unote       "$CA/app.varlorg.unote_30.apk"  4f1a9e4e8f64fae8
    ;;
esac
case "${1:-ALL}" in
  part2|ALL)
    run3 de.duenndns.gmdice      "$CA/de.duenndns.gmdice_8.apk"  f3b483fe7b7cf51b
    run3 com.darkempire78.opencalculator "$BASE/upload/opencalculator_53.apk" a976d2f9fb675cb3
    run3 jwtc.android.chess  "$BASE/upload/chess_jwtc_298.apk" b5a7a35d5fe0564b
    ;;
esac
case "${1:-ALL}" in
  telegram|ALL)
    # No byte anchor recorded for Telegram (REAL_APP_CONTENT verdict app):
    # record x3 consistency + verdict facts.
    run3 org.telegram.messenger.web "$BASE/upload/telegram_official.apk" none
    ;;
esac
echo "cont18 anchors part ${1:-ALL} done"
