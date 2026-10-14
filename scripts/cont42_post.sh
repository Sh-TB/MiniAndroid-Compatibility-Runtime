#!/usr/bin/env bash
# cont42_post.sh — CONT-42 Phase-5 POST evidence on the POST binary (the
# F-NEW-304 fragment pending-op drain + PreferenceFragment laws):
#  (a) frag_tx_probe rows FT-01..11 must ALL PASS (transaction record,
#      commit id, the full lifecycle ladder, identity getters, and the
#      fragment view attached into the container);
#  (b) com.tananaev.calculator v1.10 — the FragmentTransaction.commit
#      REC-MISS must be GONE, PrefsFragment must reach onCreateView, the
#      preference rows must build, and the frame must carry app draw ops.
#      Whatever the honest resulting frame is, it is recorded verbatim.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
FTAPK=$BASE/tmp/w4_probebuild/frag_tx_probe/frag_tx_probe.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
OUT=$BASE/run/cont42/post
mkdir -p "$OUT"
echo "POST binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"
for i in 1 2 3; do
  o="$OUT/ft_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$FTAPK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -cE "^FT-[0-9]+.*\|PASS\|" "$o/run.log" 2>/dev/null)
  fail=$(grep -cE "^FT-[0-9]+.*\|FAIL\|" "$o/run.log" 2>/dev/null)
  echo "POST ft_r$i rc=$rc FT-PASS=$pass FT-FAIL=$fail"
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
  f304=$(grep -c "F-NEW-304" "$o/run.log" 2>/dev/null || echo 0)
  echo "POST tanana_r$i rc=$rc sha=$sha commit-REC-MISS=$recmiss F304-lines=$f304 $verdict"
done
