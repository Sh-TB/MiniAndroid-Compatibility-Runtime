#!/usr/bin/env bash
# cont39_pre.sh — CONT-39 Phase-2 PRE evidence: the cpipe PC-01..04 rows
# (TextView.setTextColor → getCurrentTextColor state round-trip) on the
# CURRENT binary (the CONT-38 record). The standing CONT-38 runs recorded
# 13/4 (PC rows FAIL x3); this reproduces it fresh on the frozen binary.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
APK=$BASE/tmp/w4_probebuild/colorpipe_probe/colorpipe_probe.apk
OUT=$BASE/run/cont39/pre
mkdir -p "$OUT"
echo "PRE binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"
for i in 1 2 3; do
  o="$OUT/r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$APK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  pcfail=$(grep -E "PC-0[1-4]\|FAIL" "$o/run.log" | wc -l)
  echo "PRE r$i rc=$rc PASS=$pass FAIL=$fail PC-fails=$pcfail"
  grep -E "PC-0[1-4]\|" "$o/run.log" | head -4
done
