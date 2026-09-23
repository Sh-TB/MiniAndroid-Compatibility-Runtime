#!/usr/bin/env bash
# s83_snake_proof.sh — Snake Deluxe completion proof at S83 HEAD.
# START tap → snake runs (real ticks) → wall death → GAME OVER dialog →
# Restart tap → second life. Frame-captured end to end.
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
APK=$ROOT/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk
OUT=$ROOT/run/s83_snake_proof
rm -rf "$OUT"; mkdir -p "$OUT"

# S80 button coordinates (layout geometry — unchanged by the S83 canvas law)
"$ENG" run --execution-mode real-dalvik --frames 26 --frame-delay 420 -o "$OUT" \
  --tap "540,1500@4" \
  --tap "539,1632@20" \
  --tap "540,1500@24" \
  "$APK" > "$OUT/engine.log" 2>&1
rc=$?
echo "rc=$rc"
ls "$OUT/frames" | tail -3
