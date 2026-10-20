#!/usr/bin/env bash
# cont125_sweep.sh — CONT-125 Train 2: F-NEW-469 fan-out sweep.
# Run every corpus app with a recorded face at the NEW binary (6bb7150a),
# compare face sha16, and census ArrayStoreException before/after semantics.
# Any FACE_CHANGE = real behavioral fan-out of the Train 1 law; every change
# is adjudicated honestly (never suppressed).
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
OUT=run/c125
mkdir -p "$OUT"

# name|apk|expected_face16|seconds
ROWS=(
  "flappycow|upload/flappycow_rebuilt.apk|13cf47464d9787f4|15"
  "g2048|upload/canonical_apks/com.uberspot.a2048_19.apk|59ca1526611c4622|15"
  "gmdice|upload/canonical_apks/de.duenndns.gmdice_8.apk|3891679dff449331|15"
  "bouncy|upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk|dd0c14257fa1f2af|15"
  "memory|upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk|c559b630dd8f0f0f|15"
  "tripeaks|upload/canonical_apks/tripeaks_v1.2.1_vc4.apk|b5a7a35d5fe0564b|15"
  "stopwatch|upload/canonical_apks/com.github.muellerma.stopwatch_6.apk|31ddd4d5b8e6d18e|15"
  "fishrings|upload/canonical_apks/fishrings_v1.23_vc6.apk|b5a7a35d5fe0564b|15"
  "tictactoe|upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk|NONE|30"
  "notes|upload/notes_secuso_105.apk|d0a409043ffc83a7|15"
  "chessclock|upload/chessclock_29.apk|fe3ae116|15"
  "opmt|upload/canonical_apks/opmt_v0.1.2_vc1.apk|NONE|30"
)

: > "$OUT/sweep.log"
for row in "${ROWS[@]}"; do
  IFS='|' read -r name apk want secs <<< "$row"
  [ -f "$apk" ] || { echo "$name APK-MISSING $apk" | tee -a "$OUT/sweep.log"; continue; }
  timeout $((secs*4+60)) "$B" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds "$secs" -o "$OUT/$name" > /dev/null 2> "$OUT/$name.log"
  rc=$?
  face="NO_SCREENSHOT"
  [ -f "$OUT/$name/screenshot.png" ] && face=$(sha256sum "$OUT/$name/screenshot.png" | cut -c1-16)
  aioo=$(grep -c "ArrayStoreException" "$OUT/$name.log" 2>/dev/null || echo 0)
  if [ "$want" = "NONE" ]; then
    verdict="NEW-EVIDENCE face=$face rc=$rc"
  elif [ "$face" = "$want" ]; then
    verdict="MATCH"
  else
    verdict="FACE-CHANGE want=$want got=$face"
  fi
  echo "$name rc=$rc aioobe=$aioo $verdict" | tee -a "$OUT/sweep.log"
done
