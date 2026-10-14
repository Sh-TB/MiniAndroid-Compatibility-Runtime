#!/usr/bin/env bash
# cont63_regression.sh — the FULL 11-row anchor wall ×3 at the F-NEW-351
# binary (633e231b lineage). Wants = the recorded CONT-62 wall (run/cont62/
# regression recomputed) + the dooz180 intentional re-pin c94da5a928ea213b.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont63/regression
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apk> <want|none>
  local label="$1" apk="$2" want="$3"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 135 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$? sha verdict="recorded"
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  if [ "$want" != "none" ]; then verdict="DRIFT"; [ "$sha" = "$want" ] && verdict="MATCH"; fi
  echo "REG $label rc=$rc sha=$sha want=$want $verdict"
}

A=$BASE/upload
for i in 1 2 3; do
  run1 "csw_r$i"        "$A/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk" d3c26b73ee21e571
  run1 "dooz_r$i"       "$A/canonical_apks/io.github.yamin8000.dooz_23.apk"           31ddd4d5b8e6d18e
  run1 "flappycow_r$i"  "$A/flappycow_rebuilt.apk"                                    13cf47464d9787f4
  run1 "g2048_r$i"      "$A/s80_games/build_2048/g2048_v1.0_vc1.apk"                  59ca1526611c4622
  run1 "gmdice_r$i"     "$A/canonical_apks/de.duenndns.gmdice_8.apk"                  3891679dff449331
  run1 "microtimer_r$i" "$A/canonical_apks/dubrowgn.microtimer_8.apk"                 55343bbec712618d
  run1 "opencalc_r$i"   "$A/opencalculator_53.apk"                                    f25b754c4565c38b
  run1 "simplecalc_r$i" "$A/cont54_refetch/com.simplemobiletools.calculator_8.apk"    341b9cec89d8f182
  run1 "tanana_r$i"     "$A/cont54_refetch/com.tananaev.calculator_11.apk"            afe0bd8dd4d09ca6
  run1 "tttdeluxe_r$i"  "$A/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"        af6094295ecb50e3
  run1 "unote_r$i"      "$A/canonical_apks/app.varlorg.unote_30.apk"                  90a67cc1ddda57b7
done
# dooz180 x3 — the INTENTIONAL F-NEW-351 re-pin (icons render)
for i in 1 2 3; do
  o="$OUT/dooz180_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 400 "$BIN" run "$A/canonical_apks/io.github.yamin8000.dooz_23.apk" --width 1080 --height 1920 --frames 5 --max-seconds 180 -o "$o" > "$o/run.log" 2>&1
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  verdict="DRIFT"; [ "$sha" = "c94da5a928ea213b" ] && verdict="MATCH-NEW"
  echo "REG dooz180_r$i rc=$? sha=$sha want=c94da5a928ea213b $verdict"
done
echo "WALL DONE"
