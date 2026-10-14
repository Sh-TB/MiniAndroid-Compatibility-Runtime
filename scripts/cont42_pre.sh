#!/usr/bin/env bash
# cont42_pre.sh — CONT-42 Phase-4 PRE evidence on the PRE binary (the
# pre-F-NEW-304 build of origin/main 3355f2f1):
#  (a) frag_tx_probe (com.probe.fragtx) — the FT-01..04 transaction rows
#      must FAIL/stop early and the fragment lifecycle rows must never
#      fire (the recorded pre-law face: ops dropped, commit → 0);
#  (b) com.tananaev.calculator v1.10 — the recorded CONT-41 POST face
#      (PARTIAL, Errors=0, REC-MISS FragmentTransaction.commit blocker,
#      DEFAULT_BACKGROUND_ONLY verdict) must reproduce ×3.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
FTAPK=$BASE/tmp/w4_probebuild/frag_tx_probe/frag_tx_probe.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
OUT=$BASE/run/cont42/pre
mkdir -p "$OUT"
echo "PRE binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"
for i in 1 2 3; do
  o="$OUT/ft_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$FTAPK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -cE "^FT-[0-9]+.*\|PASS\|" "$o/run.log" 2>/dev/null)
  fail=$(grep -cE "^FT-[0-9]+.*\|FAIL\|" "$o/run.log" 2>/dev/null)
  echo "PRE ft_r$i rc=$rc FT-PASS=$pass FT-FAIL=$fail"
  grep -E "^FT-" "$o/run.log" | head -14
done
for i in 1 2 3; do
  o="$OUT/tanana_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$TANANA" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  recmiss=$(grep -c "REC-MISS Landroid/app/FragmentTransaction;.commit" "$o/run.log" 2>/dev/null || echo 0)
  verdict=$(grep -oE "verdict=[A-Z_]+" "$o/run.log" 2>/dev/null | head -1)
  echo "PRE tanana_r$i rc=$rc sha=$sha commit-REC-MISS=$recmiss $verdict"
done
