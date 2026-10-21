#!/usr/bin/env bash
# cont150_f473_probe.sh — F-NEW-473 root-layer marking path decode.
# Q: do the static xref candidates (Lgb1;.{c,d,f,m}, Lpz0;.g1/m1, Lrv;.a) have
#    ANY runtime entries in the dooz draw window? If all zero -> climb one more
#    level: the marking caller itself never runs.
# Also: FIELD-TRACE Ltv0; to re-anchor the root layer flag behavior at the
#    current binary (b0cc28e4, rebuild #8, behavior-verified 9/9).
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
mkdir -p run/c150

for cand in "Lgb1;" "Lpz0;" "Lrv;"; do
  tag=$(echo "$cand" | tr -d 'L;')
  echo "== ARG-TRACE $cand =="
  MINIANDROID_ARG_TRACE="$cand" timeout 170 "$B" run "$CA/io.github.yamin8000.dooz_23.apk" \
    --width 1080 --height 1920 --frames 5 --max-seconds 25 -o "run/c150/f473_$tag" \
    > /dev/null 2> "run/c150/f473_$tag.log"
  echo "rc=$? log_lines=$(wc -l < run/c150/f473_$tag.log) argtrace_lines=$(grep -c 'ARG-TRACE' run/c150/f473_$tag.log)"
  face=$(sha256sum "run/c150/f473_$tag/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "face=$face"
  grep 'ARG-TRACE' "run/c150/f473_$tag.log" | head -8
done
