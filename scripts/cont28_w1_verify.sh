#!/bin/bash
# cont28_w1_verify.sh — verify the F516 null-contract battery on the 3
# DEX-decoded census roots (webstack/audiobook/wocheneinkauf).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont28/f141
mkdir -p "$OUT"
for t in webstack audiobook wocheneinkauf; do
  case "$t" in
    webstack)      APK="$BASE/upload/fdroid_batch/com.chiranth7.webstack_6.apk"; PKG=com.chiranth7.webstack;;
    audiobook)     APK="$BASE/upload/fdroid_batch/de.ph1b.audiobook_5410002.apk"; PKG=de.ph1b.audiobook;;
    wocheneinkauf) APK="$BASE/upload/fdroid_batch/app.wocheneinkauf_199.apk"; PKG=app.wocheneinkauf;;
  esac
  ST="$OUT/store_$t"
  if [ ! -d "$ST" ]; then
    "$BIN" install "$APK" --data-root "$ST" > "$OUT/${t}_install.log" 2>&1
    echo "$t install rc=$?"
  fi
  o="$OUT/$t"; mkdir -p "$o"
  "$BIN" run --package "$PKG" --data-root "$ST" \
    --max-seconds 90 --frames 20 -o "$o" > "$o/run.log" 2> "$o/diag.txt"
  echo "== $t run rc=$?"
  echo "  law hits: $(grep -c 'F516-L' "$o/diag.txt")"
  echo "  f141 face STILL PRESENT: $(grep -c 'f141-null-recv' "$o/diag.txt")"
  echo "  clinit results: $(grep -oE '\[CLASS_INIT\] class=(Lru1;|Lox5;|Lqm;) method=<clinit> result=[A-Z]+' "$o/diag.txt" | tr '\n' ' ')"
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "  screenshot sha16=$s"
  echo "  first missing stage: $(grep -oE 'first_missing=[A-Z_]+' "$o/run.log" | head -1)"
  echo "  uncaught: $(grep -oE 'F-016 exception-honesty: [0-9]+ uncaught' "$o/run.log" | head -1)"
done
