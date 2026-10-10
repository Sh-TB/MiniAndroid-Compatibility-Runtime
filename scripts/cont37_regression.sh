#!/usr/bin/env bash
# cont37_regression.sh — CONT-37 Phase-5 regression gate at the F-NEW-298
# binary. The binary CHANGED this wave (three coordinated generic laws:
# Canvas.getClipBounds (the Compose paragraph-paint gate),
# StaticLayout$Builder setText/setTextDirection prefix-conflation (the
# payload clobber), and the FRAME-HONESTY law (an in-draw halt is never
# presented — the P1-6 extension recorded PENDING in CONT-36 §6)).
# Anchor expectations: 7/8 anchors UNCHANGED (their draws never halt
# in-window; KEEP=0 — zero drift). dooz LEGITIMATELY MOVES to the honest
# keep-empty state (its boot composition takes ~15.3 s of engine time; the
# 15 s budget halts the draw mid-way; the old 250-gray anchor was the
# DISHONEST presentation of that unfinished frame — CONT-36 §6 decode).
# composeStopwatch moves to its first honest content frame (cards + text).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont37/regression
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
SIMPLECALC=$BASE/tmp/cont35_apks/simplecalc_8.apk
CSW=$BASE/tmp/cont35_apks/composeStopwatch_1009011.apk

# ---- probe battery (rebuilt fresh; run/ artifacts reset-liable) ----
bash $BASE/scripts/cont21_build_probes.sh > "$OUT/probe_build.log" 2>&1 \
  || echo "PROBE BUILD FAILED (see probe_build.log)"
bash $BASE/scripts/w4_build_probes.sh > "$OUT/w4_probe_build.log" 2>&1 \
  || echo "W4 PROBE BUILD FAILED (see w4_probe_build.log)"
bash $BASE/scripts/cont30_build_probe.sh > "$OUT/f286_probe_build.log" 2>&1 \
  || echo "F286 PROBE BUILD FAILED (see f286_probe_build.log)"

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

# fnew298 needs the RUNNER-SIDE pixel row (the app cannot read the
# framebuffer): the final screenshot's top-left 8x8 block must be the
# frame-1 green 0xFF00FF00 (the keep-previous marker).
probe_fnew298() {
  local label="fnew298" apk="$BASE/tmp/w4_probebuild/fnew298_probe/fnew298_probe.apk"
  local o="$OUT/probe_$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local corner keep
  corner=$(python3 -c "
from PIL import Image
im = Image.open('$o/screenshot.png').convert('RGB')
ok = all(im.getpixel((x,y))==(0,255,0) for x in range(8) for y in range(8))
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo FAIL)
  keep=$(grep -c "F298-KEEP" "$o/run.log" 2>/dev/null || echo 0)
  if [ "$corner" = "PASS" ]; then
    echo "F298|KEEP-CORNER|PASS|final frame keeps the frame-1 green marker (KEEP=$keep)" >> "$o/run.log"
  else
    echo "F298|KEEP-CORNER|FAIL|final frame lost the frame-1 marker (KEEP=$keep)" >> "$o/run.log"
  fi
  local pass fail
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PROBE $label rc=$rc PASS=$pass FAIL=$fail (KEEP=$keep corner=$corner)"
}

case "${1:-all}" in
anchors)
  for i in 1 2 3; do
    run1 "dooz_r$i"       "$DOOZ"      31ddd4d5b8e6d18e
    run1 "microtimer_r$i" "$MICRO"     da73010a37dd0189
    run1 "unote_r$i"      "$UNOTE"     4f1a9e4e8f64fae8
    run1 "gmdice_r$i"     "$GMDICE"    f3b483fe7b7cf51b
    run1 "opencalc_r$i"   "$OPENCALC"  a976d2f9fb675cb3
    run1 "tttdeluxe_r$i"  "$TTT"       af6094295ecb50e3
    run1 "flappycow_r$i"  "$FLAPPY"    13cf47464d9787f4
    run1 "g2048_r$i"      "$G2048"     59ca1526611c4622
  done
  ;;
target)
  for i in 1 2 3; do
    run1 "csw_r$i" "$CSW" bbaf8f76308dc267
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
  probe1 ckey   "$BASE/tmp/w4_probebuild/classkey_probe/classkey_probe.apk"
  probe1 fnew252 "$BASE/tmp/w4_probebuild/fnew252_probe/fnew252_probe.apk"
  probe1 fnew290 "$BASE/tmp/w4_probebuild/fnew290_probe/fnew290_probe.apk"
  probe1 fnew291 "$BASE/tmp/w4_probebuild/fnew291_probe/fnew291_probe.apk"
  probe1 fnew292 "$BASE/tmp/w4_probebuild/fnew292_probe/fnew292_probe.apk"
  probe1 fnew293 "$BASE/tmp/w4_probebuild/fnew293_probe/fnew293_probe.apk"
  probe1 fnew294 "$BASE/tmp/w4_probebuild/fnew294_probe/fnew294_probe.apk"
  probe1 fnew295 "$BASE/tmp/w4_probebuild/fnew295_probe/fnew295_probe.apk"
  probe1 fnew296 "$BASE/tmp/w4_probebuild/fnew296_probe/fnew296_probe.apk"
  probe1 fnew297 "$BASE/tmp/w4_probebuild/fnew297_probe/fnew297_probe.apk"
  probe_fnew298
  ;;
control)
  for i in 1 2 3; do
    run1 "simplecalc_r$i" "$SIMPLECALC" none
  done
  ;;
*)
  "$0" anchors
  "$0" target
  "$0" probes
  "$0" control
  echo "REGRESSION DONE"
  ;;
esac
