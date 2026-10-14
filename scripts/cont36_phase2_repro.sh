#!/usr/bin/env bash
# cont36_phase2_repro.sh — CONT-36 Phase 2: independently reproduce the
# CONT-35 evidence from the verified remote source (HEAD 1cc38daa, binary
# 6508a51d01b54280). The three new probes x3 + composeStopwatch x3 +
# SimpleCalc control x3. Full anchors gate runs separately
# (cont35_regression.sh anchors) to keep wall time bounded.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont36
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <outdir> <apk>
  local o="$1" apk="$2"
  rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  echo $?
}

echo "== PROBES x3 (fnew294/295/296) =="
for p in fnew294 fnew295 fnew296; do
  apk=$BASE/tmp/w4_probebuild/${p}_probe/${p}_probe.apk
  for i in 1 2 3; do
    o=$OUT/${p}_post_r$i
    rc=$(run1 "$o" "$apk")
    pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
    fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
    echo "PROBE $p r$i rc=$rc PASS=$pass FAIL=$fail"
  done
done

echo "== composeStopwatch x3 =="
CSW=$BASE/tmp/cont35_apks/composeStopwatch_1009011.apk
for i in 1 2 3; do
  o=$OUT/csw_r$i
  rc=$(run1 "$o" "$CSW")
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  n409=$(grep -c "pc=409" "$o/run.log" 2>/dev/null || true)
  njd1=$(grep -c "Ljd1;.\x3Cclinit\x3E pc=6" "$o/run.log" 2>/dev/null || true)
  nb1=$(grep -c "Lb1;.n pc=0" "$o/run.log" 2>/dev/null || true)
  echo "CSW r$i rc=$rc sha=$sha pc409=$n409 ljd1=$njd1 lb1=$nb1"
done

echo "== SimpleCalc control x3 =="
SC=$BASE/tmp/cont35_apks/simplecalc_8.apk
for i in 1 2 3; do
  o=$OUT/simplecalc_r$i
  rc=$(run1 "$o" "$SC")
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "SIMPLECALC r$i rc=$rc sha=$sha"
done
echo "PHASE2 DONE"
