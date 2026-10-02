#!/bin/bash
# F-NEW-232/233 regression battery (goldens + gates, file-sha convention)
cd /home/z/my-project/miniandroid
OUT=run/f233_regress; rm -rf "$OUT"; mkdir -p "$OUT"
run1() { # name apk extra-args...
  local n="$1" apk="$2"; shift 2
  local o="$OUT/$n"; mkdir -p "$o"
  timeout 300 ./build/miniandroid run "$apk" "$@" -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local st=$(grep -m1 "^Status:" "$o/run.log" | cut -c9-30)
  echo "$n | rc=$rc | sha=$s | $st"
}
run3() { local n="$1" apk="$2"; shift 2
  local s=""
  for i in 1 2 3; do
    local o="$OUT/${n}_r$i"; mkdir -p "$o"
    timeout 300 ./build/miniandroid run "$apk" "$@" -o "$o" > /dev/null 2>&1
    s="$s $(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)"
  done
  echo "$n 3-run:$s"
}
echo "== GOLDENS (x3 determinism) =="
run3 dooz       /tmp/my-project/apk_cache/corpus/dooz.apk
run3 microtimer /tmp/my-project/apk_cache/dubrowgn.microtimer_8.apk
run3 unote      /tmp/my-project/apk_cache/app.varlorg.unote_30.apk
echo "== GATES =="
run3 opencalc   /home/z/my-project/upload/opencalculator_53.apk
run1 forkgram   /home/z/my-project/upload/forkgram_709208.apk
echo "== SENTINEL-GAP TITLES (plain runs now honest) =="
run1 sudoku     /home/z/my-project/upload/sudoku_secuso_101.apk
run1 fishrings  /home/z/my-project/upload/canonical_apks/fishrings_v1.23_vc6.apk
echo "== TELEGRAM (§6) =="
run1 tg_official /home/z/my-project/upload/telegram_official.apk --max-seconds 240
