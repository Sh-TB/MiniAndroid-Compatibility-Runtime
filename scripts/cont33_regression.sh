#!/usr/bin/env bash
# cont33_regression.sh — CONT-33 Phase-4 regression gate at the F-NEW-291/292 binary.
# The binary CHANGED this wave (String.format Locale overload + libcore
# UUID/Enum hierarchy rows + per-hop platform consult in dalvik_class_assignable),
# so the full gate runs: 8 frozen anchors x3 byte-exact + probe battery
# (incl. fnew291/fnew292) + Track B control (Simple Calculator x3).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont33/regression
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
  echo "REG $label rc=$rc sha=$sha want=$want $verdict"
}

DOOZ=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
MICRO=$BASE/upload/canonical_apks/dubrowgn.microtimer_8.apk
UNOTE=$BASE/upload/canonical_apks/app.varlorg.unote_30.apk
GMDICE=$BASE/upload/canonical_apks/de.duenndns.gmdice_8.apk
OPENCALC=$BASE/upload/opencalculator_53.apk
TTT=$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk
FLAPPY=$BASE/upload/flappycow_rebuilt.apk
G2048=$BASE/upload/s80_games/build_2048/g2048_v1.0_vc1.apk
SIMPLECALC=$BASE/tmp/cont30w_apks/simplecalc_8.apk

# ---- probe battery (rebuilt fresh this wave; run/ artifacts reset-liable) ----
bash $BASE/scripts/cont21_build_probes.sh > "$OUT/probe_build.log" 2>&1 \
  || echo "PROBE BUILD FAILED (see probe_build.log)"
bash $BASE/scripts/w4_build_probes.sh > "$OUT/w4_probe_build.log" 2>&1 \
  || echo "W4 PROBE BUILD FAILED (see w4_probe_build.log)"

probe1() { # probe1 <label> <apk>
  local label="$1" apk="$2"
  local o="$OUT/probe_$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local pass fail
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PROBE $label rc=$rc PASS=$pass FAIL=$fail"
}

case "${1:-all}" in
anchors)
  for i in 1 2 3; do
    run1 "dooz_r$i"       "$DOOZ"      d602648e8e401895
    run1 "microtimer_r$i" "$MICRO"     da73010a37dd0189
    run1 "unote_r$i"      "$UNOTE"     4f1a9e4e8f64fae8
    run1 "gmdice_r$i"     "$GMDICE"    f3b483fe7b7cf51b
    run1 "opencalc_r$i"   "$OPENCALC"  a976d2f9fb675cb3
    run1 "tttdeluxe_r$i"  "$TTT"       af6094295ecb50e3
    run1 "flappycow_r$i"  "$FLAPPY"    13cf47464d9787f4
    run1 "g2048_r$i"      "$G2048"     59ca1526611c4622
  done
  ;;
probes)
  probe1 fcol  "$BASE/run/w7/fcol.apk"
  probe1 f259  "$BASE/run/w7/f259.apk"
  probe1 f259g "$BASE/run/w7/f259g.apk"
  probe1 f266  "$BASE/run/w8/f266.apk"
  probe1 f268  "$BASE/run/cont18g/f268.apk"
  probe1 fnew253 "$BASE/tmp/w4_probebuild/fnew253_probe/fnew253_probe.apk"
  probe1 fnew286 "$BASE/tmp/cont30_probebuild/fnew286_probe/fnew286_probe.apk"
  probe1 fnew289 "$BASE/tmp/w4_probebuild/fnew289_probe/fnew289_probe.apk"
  probe1 fnew252 "$BASE/tmp/w4_probebuild/fnew252_probe/fnew252_probe.apk"
  probe1 fnew290 "$BASE/tmp/w4_probebuild/fnew290_probe/fnew290_probe.apk"
  probe1 fnew291 "$BASE/tmp/w4_probebuild/fnew291_probe/fnew291_probe.apk"
  probe1 fnew292 "$BASE/tmp/w4_probebuild/fnew292_probe/fnew292_probe.apk"
  ;;
control)
  for i in 1 2 3; do
    run1 "simplecalc_r$i" "$SIMPLECALC" none
  done
  ;;
*)
  "$0" anchors
  "$0" probes
  "$0" control
  echo "REGRESSION DONE"
  ;;
esac
