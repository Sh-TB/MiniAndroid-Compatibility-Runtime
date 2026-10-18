#!/usr/bin/env bash
# cont99_tr_run.sh — paired deterministic runs for the CONT-99 T2 probe.
# Usage: cont99_tr_run.sh <tag>   (tag = pre | post)
# Each run: 1080x1920, 5 frames, 30s budget, ONE deterministic tap.
set -uo pipefail
cd /home/z/my-project
BIN=${BIN:-miniandroid/build/miniandroid}
APK=run/cont99/c99tr.apk
TAG=$1
OUT=run/cont99/tr_${TAG}
mkdir -p "$OUT"

run_case() { # name [tap args...]
  local name=$1; shift
  local o="$OUT/$name"; rm -rf "$o"; mkdir -p "$o"
  if [ $# -gt 0 ]; then
    timeout 120 "$BIN" run "$APK" --width 1080 --height 1920 --frames 5 \
      --max-seconds 30 -o "$o" "$@" > "$o/run.log" 2>&1
  else
    timeout 120 "$BIN" run "$APK" --width 1080 --height 1920 --frames 5 \
      --max-seconds 30 -o "$o" > "$o/run.log" 2>&1
  fi
  echo "== $name =="
  rg -o "\[C99-(FRAME|LOC|TX|SC|ROT|SCRLL|DENS|INSET|TAP|COUNT|VER|DONE|ERR)\].*" \
     "$o/run.log" | sed 's/^/  /'
}

run_case control --tap 150,75
run_case translation --tap 110,340
run_case scale --tap 120,650
run_case scroll --tap 100,930
run_case notap ""
echo "RUNS DONE ($TAG)"
