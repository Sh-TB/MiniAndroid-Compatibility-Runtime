#!/bin/bash
# cont21_family_sweep.sh — post-fix re-run of the P1/P2 cluster targets
# (dooz, opencalc, stopwatch, telegram, forkgram) at the fixed binary +
# canonical anchors x3 regression gate.
# Usage: bash scripts/cont21_family_sweep.sh [sweep|anchors|probes]
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont21
CA=$BASE/upload/canonical_apks
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # label apk outdir
  # CONT-22 audit fix: `local` resets $?, so declare locals BEFORE the engine
  # call — the previous order always reported rc=0 (bogus; found in the
  # CONT-22 CONT21_AUDIT, engine law = exit 0 iff Status==SUCCESS).
  local label="$1" apk="$2" o="$OUT/$3" sha rc
  rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "SWEEP $label rc=$rc sha=$sha"
}

run_anchor3() { # pkg apk want
  local pkg="$1" apk="$2" want="$3"
  local store="$OUT/store_$pkg"
  [ -d "$store" ] || "$BIN" install "$apk" --data-root "$store" > /dev/null 2>&1
  for i in 1 2 3; do
    local o="$OUT/anchor_${pkg}_$i"; rm -rf "$o"; mkdir -p "$o"
    timeout 300 "$BIN" run --package "$pkg" --data-root "$store" \
      --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
    local sha
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    [ "$sha" = "$want" ] && echo "ANCHOR $pkg run$i sha=$sha MATCH" \
                          || echo "ANCHOR $pkg run$i sha=$sha RECORDED=$want DRIFT"
  done
}

case "${1:-ALL}" in
sweep|ALL)
  run1 dooz      "$CA/dooz_23_toplevel.apk"        sweep_dooz
  run1 opencalc  "$BASE/upload/opencalculator_53.apk" sweep_opencalc
  run1 stopwatch "$CA/com.github.muellerma.stopwatch_6.apk" sweep_stopwatch
  run1 telegram  "$BASE/upload/telegram_official.apk"  sweep_telegram
  run1 forkgram  "$BASE/upload/forkgram_709208.apk"    sweep_forkgram
  ;;
esac
case "${1:-ALL}" in
anchors|ALL)
  run_anchor3 io.github.yamin8000.dooz "$CA/dooz_23_toplevel.apk" d602648e8e401895
  run_anchor3 dubrowgn.microtimer      "$CA/dubrowgn.microtimer_8.apk" da73010a37dd0189
  run_anchor3 app.varlorg.unote        "$CA/app.varlorg.unote_30.apk"  4f1a9e4e8f64fae8
  run_anchor3 de.duenndns.gmdice       "$CA/de.duenndns.gmdice_8.apk"  f3b483fe7b7cf51b
  run_anchor3 com.darkempire78.opencalculator "$BASE/upload/opencalculator_53.apk" a976d2f9fb675cb3
  run_anchor3 com.miniandroid.tictactoedeluxe "$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk" af6094295ecb50e3
  ;;
esac
