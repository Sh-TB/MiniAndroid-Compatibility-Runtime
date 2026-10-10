#!/usr/bin/env bash
# cont41_post.sh — CONT-41 Phase-2 POST evidence on the POST binary (the
# Notification$Builder fluent-chain law in dalvik_engine.cpp):
# (a) notif_builder_probe rows NB-01..08 must ALL PASS (was: fluent-chain
#     rows FAIL on PRE),
# (b) com.tananaev.calculator v1.10 — the NotificationCompat$Builder
#     pc=64 NPE must be gone; the resulting frame is recorded as the new
#     honest state whatever it is (content or the next frontier's face).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
NBAPK=$BASE/tmp/w4_probebuild/notif_builder_probe/notif_builder_probe.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
OUT=$BASE/run/cont41/post
mkdir -p "$OUT"
echo "POST binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"
for i in 1 2 3; do
  o="$OUT/nb_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$NBAPK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "POST nb_r$i rc=$rc PASS=$pass FAIL=$fail"
  grep -E "^NB-0[1-8]\|" "$o/run.log" | head -8
done
for i in 1 2 3; do
  o="$OUT/tanana_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$TANANA" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  npe=$(grep -c "setSmallIcon" "$o/run.log" 2>/dev/null || echo 0)
  uncaught=$(grep -c "UNCAUGHT\|uncaught" "$o/run.log" 2>/dev/null || echo 0)
  echo "POST tanana_r$i rc=$rc sha=$sha setSmallIcon-hits=$npe uncaught=$uncaught"
done
