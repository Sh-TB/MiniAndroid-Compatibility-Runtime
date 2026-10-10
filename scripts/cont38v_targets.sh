#!/usr/bin/env bash
# cont38v_targets.sh — CONT-38v Phase-3 verification targets on the CURRENT
# verified binary (a181d7b317e015c8, CONT-37 record): the friend-report
# controls (dooz, SimpleCalc, tananaev calculator) + headingcalc re-supplied
# SHA-exact. Fresh baseline records for anything without a current-era
# expectation; recorded hashes compared against the historical goldens.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont38v/targets
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apkpath> <want-sha16|none>
  local label="$1" apk="$2" want="${3:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local verdict="DRIFT"
  [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$want" = "none" ] && verdict="recorded"
  echo "RUN $label rc=$rc sha=$sha want=$want $verdict"
}

DOOZ=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
SIMPLECALC=$BASE/tmp/cont35_apks/simplecalc_8.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
HEADING=$BASE/tmp/headingcalculator_1.apk

case "${1:-all}" in
dooz)      for i in 1 2 3; do run1 "dooz_r$i" "$DOOZ" 31ddd4d5b8e6d18e; done ;;
simplecalc) for i in 1 2 3; do run1 "scalc_r$i" "$SIMPLECALC" 7960bce447ac6d8f; done ;;
tananaev)  for i in 1 2 3; do run1 "tanana_r$i" "$TANANA" none; done ;;
heading)   for i in 1 2 3; do run1 "heading_r$i" "$HEADING" none; done ;;
all)
  for i in 1 2 3; do
    run1 "dooz_r$i"    "$DOOZ"      31ddd4d5b8e6d18e
    run1 "scalc_r$i"   "$SIMPLECALC" 7960bce447ac6d8f
    run1 "tanana_r$i"  "$TANANA"    none
    run1 "heading_r$i" "$HEADING"   none
  done
  ;;
esac
