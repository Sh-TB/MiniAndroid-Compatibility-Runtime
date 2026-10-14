#!/usr/bin/env bash
# cont41_pre.sh — CONT-41 Phase-2 PRE evidence on the frozen PRE binary:
# (a) the notif_builder_probe rows NB-01..08 (Notification$Builder fluent
#     chain — the law does not exist yet),
# (b) the recorded CONT-38v frontier app com.tananaev.calculator v1.10
#     (NotificationCompat$Builder.<init> pc=64 NPE →
#     DEFAULT_BACKGROUND_ONLY d602648e8e401895).
# PRE binary: run/cont41/miniandroid_pre_d3d6a5412a696122 (pre-law build of
# origin/main 43a3db9d; frame-hash regression re-baselined this session).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/run/cont41/miniandroid_pre_d3d6a5412a696122
NBAPK=$BASE/tmp/w4_probebuild/notif_builder_probe/notif_builder_probe.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
OUT=$BASE/run/cont41/pre
mkdir -p "$OUT"
echo "PRE binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"
for i in 1 2 3; do
  o="$OUT/nb_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$NBAPK" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PRE nb_r$i rc=$rc PASS=$pass FAIL=$fail"
  grep -E "^NB-0[1-8]\|" "$o/run.log" | head -8
done
for i in 1 2 3; do
  o="$OUT/tanana_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$TANANA" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  npe=$(grep -c "setSmallIcon" "$o/run.log" 2>/dev/null || echo 0)
  echo "PRE tanana_r$i rc=$rc sha=$sha setSmallIcon-hits=$npe"
done
