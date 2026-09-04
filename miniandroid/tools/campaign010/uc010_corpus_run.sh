#!/bin/bash
# CAMPAIGN 010 R23 — run the 5 new corpus APKs, honest per-criteria evidence.
cd /home/z/my-project/repo/miniandroid
OUT=/tmp/uc010/corpus; mkdir -p $OUT
CACHE=~/.cache/miniandroid/apks
nonwhite() { python3 -c "
from PIL import Image
im = Image.open('$1').convert('RGB')
print(sum(1 for p in im.getdata() if p != (255,255,255)))
" 2>/dev/null || echo "ERR"; }

for apk in "$CACHE"/com.byagowi.persiancalendar_*.apk "$CACHE"/de.mm20.launcher2.release_*.apk \
           "$CACHE"/de.dennisguse.opentracks_*.apk "$CACHE"/net.gsantner.markor_*.apk \
           "$CACHE"/org.isoron.uhabits_*.apk; do
  base=$(basename "$apk" .apk)
  echo "=== $base ==="
  timeout 120 ./build/miniandroid run -o "$OUT/$base" "$apk" > "$OUT/$base.log" 2>&1
  ec=$?
  img=$(ls "$OUT/$base"/screenshot.png 2>/dev/null | head -1)
  nw=$( [ -n "$img" ] && nonwhite "$img" || echo "no-img" )
  dex=$(grep -c "METHOD-IN" "$OUT/$base.log" 2>/dev/null | head -1)
  status=$(grep -m1 "Status:" "$OUT/$base/report.md" 2>/dev/null | sed 's/.*Status: //')
  echo "  exit=$ec status=${status:-?} nonwhite=$nw method_in=$dex"
done