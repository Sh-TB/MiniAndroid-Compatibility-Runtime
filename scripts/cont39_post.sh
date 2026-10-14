#!/usr/bin/env bash
# cont39_post.sh — CONT-39 Phase-4 POST evidence: the cpipe probe on the
# FIXED binary. Gate: PC-01..04 all PASS x3, the TR/SC rows and the rest
# of the standing battery unchanged, then targets + full regression.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
APK=$BASE/tmp/w4_probebuild/colorpipe_probe/colorpipe_probe.apk
OUT=$BASE/run/cont39/post
mkdir -p "$OUT"
echo "POST binary: $(sha256sum $BIN | cut -c1-16)"
for i in 1 2 3; do
  o="$OUT/r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$APK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "POST r$i rc=$rc PASS=$pass FAIL=$fail"
  grep -E "PC-0[1-4]\|" "$o/run.log" | head -4
done
