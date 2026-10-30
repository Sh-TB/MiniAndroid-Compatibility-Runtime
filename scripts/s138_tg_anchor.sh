#!/usr/bin/env bash
# S138 telegram OFFICIAL anchor regression (cont121 battery law: 5 frames/60s,
# face anchor 20ac8cbbbb692e63).
set -u
cd /home/z/my-project
OUT=run/s138_tg_official_anchor
rm -rf "$OUT"; mkdir -p "$OUT"
timeout 300 ./miniandroid/build/miniandroid run upload/telegram_official.apk \
  --width 1080 --height 1920 --frames 5 --max-seconds 60 -o "$OUT" >/dev/null 2>"$OUT/anchor.log"
echo "exit=$?"
if [ -f "$OUT/screenshot.png" ]; then sha256sum "$OUT/screenshot.png" | cut -c1-16; else echo NO_SCREENSHOT; fi
