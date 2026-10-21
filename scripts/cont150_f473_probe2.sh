#!/usr/bin/env bash
# cont150_f473_probe2.sh — dispatchDraw flow depth: owner (Lhi;) + canvas holder (Ly3;)
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
mkdir -p run/c150

for cand in "Lhi;" "Ly3;" "Lj7;"; do
  tag=$(echo "$cand" | tr -d 'L;')
  MINIANDROID_ARG_TRACE="$cand" timeout 170 "$B" run "$CA/io.github.yamin8000.dooz_23.apk" \
    --width 1080 --height 1920 --frames 5 --max-seconds 25 -o "run/c150/f473p2_$tag" \
    > /dev/null 2> "run/c150/f473p2_$tag.log"
  echo "== ARG-TRACE $cand rc=$? lines=$(grep -c 'ARG-TRACE' run/c150/f473p2_$tag.log) =="
  grep 'ARG-TRACE' "run/c150/f473p2_$tag.log" | head -6
  face=$(sha256sum "run/c150/f473p2_$tag/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "face=$face"
done

echo "== FIELD-TRACE Ly3; =="
MINIANDROID_FIELD_TRACE="Ly3;" timeout 170 "$B" run "$CA/io.github.yamin8000.dooz_23.apk" \
  --width 1080 --height 1920 --frames 5 --max-seconds 25 -o "run/c150/f473p2_fld" \
  > /dev/null 2> "run/c150/f473p2_fld.log"
echo "rc=$? field_lines=$(grep -c 'FIELD-TRACE' run/c150/f473p2_fld.log)"
grep 'FIELD-TRACE' run/c150/f473p2_fld.log | head -12
