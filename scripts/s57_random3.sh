#!/usr/bin/env bash
# s57_random3.sh — generalization test: 3 apps not in the anchor set, at the
# S135 binary (62f651ba6accded3). fishrings carries a recorded REAL content
# anchor a341e3ad9092f640 (W4) — byte-match proves the fixes generalized.
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s57/random3
mkdir -p "$OUT"
run_app() {
  local name=$1 apk=$2 pkg=$3 frames=${4:-40} secs=${5:-90}
  local st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "$apk" --data-root "$st" > /dev/null 2>&1
  fi
  for i in 1 2 3; do
    local o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    "$B" run --package "$pkg" --data-root "$st" --max-seconds "$secs" --frames "$frames" -o "$o" > /dev/null 2>&1 || true
    local s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    echo "$name run$i sha=$s"
  done
}
case "${1:-all}" in
  fishrings) run_app fishrings /home/z/my-project/upload/canonical_apks/fishrings_v1.23_vc6.apk eu.veldsoft.fish.rings 400 120 ;;
  notes)     run_app notes /home/z/my-project/upload/notes_secuso_105.apk org.secuso.privacyfriendlynotes 40 90 ;;
  klondike)  run_app klondike /home/z/my-project/upload/klondike_veldsoft_3.apk eu.veldsoft.free.klondike 40 90 ;;
  all) run_app fishrings /home/z/my-project/upload/canonical_apks/fishrings_v1.23_vc6.apk eu.veldsoft.fish.rings 400 120
       run_app notes /home/z/my-project/upload/notes_secuso_105.apk org.secuso.privacyfriendlynotes 40 90
       run_app klondike /home/z/my-project/upload/klondike_veldsoft_3.apk eu.veldsoft.free.klondike 40 90 ;;
esac
