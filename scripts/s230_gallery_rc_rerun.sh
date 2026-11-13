#!/bin/bash
# S230: RC re-runs of the four README gallery demos on binary 06f98d2a9c21ea92.
# Drivers are the canonical documented schedules (S80/S98 campaigns).
set -u
cd /home/z/my-project
OUT=/tmp/s230_gallery
mkdir -p "$OUT"

run_driver () {
  local name="$1"; shift
  echo "=== $name start $(date -u +%H:%M:%S) ==="
  timeout 900 "$@" > "$OUT/$name.log" 2>&1
  echo "=== $name exit=$? end $(date -u +%H:%M:%S) ==="
}

run_driver g2048      python3 scripts/autoplay/s80_2048_autoplay.py
run_driver tetris     python3 scripts/autoplay/s80_tet_autoplay.py
run_driver snakedeluxe python3 scripts/autoplay/s80_sd_autoplay.py
run_driver minicraft  python3 scripts/autoplay/s98_minicraft_autoplay.py
echo "ALL DONE $(date -u +%H:%M:%S)"
