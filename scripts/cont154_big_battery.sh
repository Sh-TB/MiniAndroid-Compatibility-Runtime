#!/usr/bin/env bash
# cont154_big_battery.sh — big-corpus battery (fdroid_batch wave). Usage: cont154_big_battery.sh <from> <to>  (1-based indexes into sorted APK list)
# Idempotent: apps with existing rc= logs are skipped.
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
LOG=run/c154/battery.log
mkdir -p run/c154
MAPFILE=$(mktemp)
ls upload/fdroid_batch/*.apk | sort > "$MAPFILE"

wagon() { # idx apk
  local idx="$1" apk="$2"
  local base; base=$(basename "$apk"); base="${base%_*}"
  if [ -f "run/c154/$base.log" ] && grep -q 'rc=' "run/c154/$base.log" 2>/dev/null; then
    echo "== WAGON $idx $base SKIP (done) ==" >> "$LOG"; return 0
  fi
  echo "== WAGON $idx $base apk=$(basename $apk) ==" >> "$LOG"
  timeout 120 "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds 25 -o "run/c154/$base" > "run/c154/$base.out" 2> "run/c154/$base.log"
  local rc=$?
  echo "rc=$rc" >> "$LOG"
  local face="NO_SCREENSHOT"
  [ -f "run/c154/$base/screenshot.png" ] && face=$(sha256sum "run/c154/$base/screenshot.png" | cut -c1-16)
  echo "face=$face" >> "$LOG"
  local uncaught boundary png
  uncaught=$(grep -c -iE 'Uncaught|SYNTH-EXC' "run/c154/$base.log" 2>/dev/null || true)
  boundary=$(grep -c -E 'APP-BOUNDARY|APPLICATION_BOUNDARY' "run/c154/$base.log" 2>/dev/null || true)
  png=$([ -f "run/c154/$base/screenshot.png" ] && echo yes || echo no)
  echo "uncaught_or_synthexc=$uncaught boundary=$boundary png=$png" >> "$LOG"
  grep -E 'SYNTH-EXC|Uncaught|first_missing_stage|APP-BOUNDARY' "run/c154/$base.log" 2>/dev/null | head -2 | sed 's/^/  KEY: /' >> "$LOG"
}

FROM="$1"; TO="$2"
i=0
while read -r apk; do
  i=$((i+1))
  [ "$i" -lt "$FROM" ] && continue
  [ "$i" -gt "$TO" ] && break
  wagon "$i" "$apk"
done < "$MAPFILE"
rm -f "$MAPFILE"
echo "== CHUNK $FROM-$TO DONE ==" >> "$LOG"
