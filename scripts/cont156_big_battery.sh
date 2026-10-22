#!/bin/bash
# cont156_big_battery.sh — CONT-156 corpus re-battery on the new binary
# (F-NEW-486/487/488 fixes). Usage: cont156_big_battery.sh <from> <to>.
# Fresh output under run/c156/big/ (idempotent per app log).
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
mkdir -p run/c156/big
MAPFILE=$(mktemp)
ls upload/fdroid_batch/*.apk | sort > "$MAPFILE"

wagon() { # idx apk
  local idx="$1" apk="$2"
  local base; base=$(basename "$apk"); base="${base%_*}"
  if [ -f "run/c156/big/$base.log" ] && grep -q 'rc=' "run/c156/big/$base.log" 2>/dev/null; then
    echo "== WAGON $idx $base SKIP ==" >> run/c156/big/battery.log; return 0
  fi
  echo "== WAGON $idx $base apk=$(basename $apk) ==" >> run/c156/big/battery.log
  timeout 120 "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds 25 -o "run/c156/big/$base" > "run/c156/big/$base.out" 2> "run/c156/big/$base.log"
  local rc=$?
  echo "rc=$rc" >> run/c156/big/battery.log
  local uncaught boundary
  uncaught=$(grep -c -iE 'Uncaught|SYNTH-EXC' "run/c156/big/$base.log" 2>/dev/null || true)
  boundary=$(grep -c -E 'APP-BOUNDARY|APPLICATION_BOUNDARY' "run/c156/big/$base.log" 2>/dev/null || true)
  echo "uncaught_or_synthexc=$uncaught boundary=$boundary png=$([ -f run/c156/big/$base/screenshot.png ] && echo yes || echo no)" >> run/c156/big/battery.log
}

n=0
while read -r apk; do
  n=$((n+1))
  if [ "$n" -ge "$1" ] && [ "$n" -le "$2" ]; then wagon "$n" "$apk"; fi
done < "$MAPFILE"
rm -f "$MAPFILE"
echo "CHUNK $1-$2 DONE" >> run/c156/big/battery.log
