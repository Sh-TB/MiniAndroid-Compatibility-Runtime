#!/usr/bin/env bash
# cont107_probe_run.sh — run the three CONT-107 probes and print their rows.
# usage: cont107_probe_run.sh <tag>   (tag = pre|post)
set -u
cd /home/z/my-project
TAG=$1
RUN=run/c107/$TAG
mkdir -p "$RUN"

for p in c106a c106b2 c106b; do
  case $p in
    c106a)  APK=run/cont106/c106a.apk ;;
    c106b2) APK=run/c107/c106b2.apk ;;
    c106b)  APK=run/c107/c106b.apk ;;
  esac
  echo "== $p ($TAG) =="
  timeout 90 ./miniandroid/build/miniandroid run "$APK" --width 1080 --height 1920 \
    --frames 3 --max-seconds 30 -o "$RUN/$p" > /dev/null 2> "$RUN/$p.stderr"
  case $p in
    c106a)  rg -o "\[C106-.*" "$RUN/$p.stderr" ;;
    c106b2) rg -o "\[C448-.*" "$RUN/$p.stderr" ;;
    c106b)  rg -o "\[C449-.*" "$RUN/$p.stderr" ;;
  esac
done
echo "== ROOT-059/F447 lines ($TAG) =="
rg -o "\[ROOT-059\].*|\[F447-NPE\].*" "$RUN"/*.stderr | head -20 || true
