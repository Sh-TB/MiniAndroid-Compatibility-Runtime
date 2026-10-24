#!/usr/bin/env bash
# cont11_w7_controls.sh — W7 regression controls at the R-NEW-445 binary.
# Runs every runnable control app in the canonical pool x3 (canonical profile:
# install store, --trace, --max-seconds 90, --frames 40) and prints sha16 x3.
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/w7/controls
mkdir -p "$OUT"

run_one() {
  local name=$1 apk=$2 pkg=$3
  local st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "$apk" --data-root "$st" > /dev/null 2>&1
  fi
  local shas=""
  for i in 1 2 3; do
    local o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    timeout 150 "$B" run --package "$pkg" --data-root "$st" --trace \
      --max-seconds 90 --frames 40 -o "$o" > /dev/null 2>&1 || true
    local s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
  done
  echo "$name:$shas"
}

C=/home/z/my-project/upload/canonical_apks
run_one bouncy "$C/com.dozingcatsoftware.bouncy_43.apk" com.dozingcatsoftware.bouncy
run_one tictactoe "$C/com.emmanuelmess.tictactoe_3.apk" com.emmanuelmess.tictactoe
run_one gmdice "$C/de.duenndns.gmdice_8.apk" de.duenndns.gmdice
run_one stopwatch "$C/com.github.muellerma.stopwatch_6.apk" com.github.muellerma.stopwatch
run_one fishrings "$C/fishrings_v1.23_vc6.apk" com.example.fishrings
run_one secusomemory "$C/org.secuso.privacyfriendlymemory_100.apk" org.secuso.privacyfriendlymemory
run_one stacktower "$C/stack.tower3d_1.apk" com.narwhal.stacktower3d
run_one tripeaks "$C/tripeaks_v1.2.1_vc4.apk" com.glue.android.tripeaks
