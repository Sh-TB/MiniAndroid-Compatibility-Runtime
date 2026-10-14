#!/bin/bash
# cont23_baseline.sh — CONT-23 Phase 0: fresh dooz truth at the verified binary.
# - canonical dooz run x2 (rc truth, uncaught census, screenshot sha)
# - dooz anchor x2 (frozen expectation d602648e8e401895)
# rc captured IMMEDIATELY after the engine call (CONT-22 audit law).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
CA=$BASE/upload/canonical_apks
OUT=$BASE/run/cont23
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # label apk outdir extra-env
  local label="$1" apk="$2" o="$OUT/$3" sha rc
  rm -rf "$o"; mkdir -p "$o"
  env "$4" timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local unc
  unc=$(grep -c "uncaught" "$o/run.log" 2>/dev/null || true)
  local status
  status=$(grep -oE "Status[^\n]{0,40}" "$o/run.log" | head -1)
  echo "RUN $label rc=$rc sha=$sha uncaught_lines=$unc :: $status"
}

run_anchor() { # idx
  local i="$1"
  local o="$OUT/anchor_dooz_$i" sha rc pkg
  pkg=io.github.yamin8000.dooz
  local store="$OUT/store_dooz"
  [ -d "$store" ] || "$BIN" install "$CA/dooz_23_toplevel.apk" --data-root "$store" > /dev/null 2>&1
  rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run --package "$pkg" --data-root "$store" \
    --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  [ "$sha" = "d602648e8e401895" ] && echo "ANCHOR dooz run$i sha=$sha MATCH" \
    || echo "ANCHOR dooz run$i sha=$sha RECORDED=d602648e8e401895 DRIFT"
}

case "${1:-all}" in
prefix)
  run1 dooz_prefix_r1 "$CA/dooz_23_toplevel.apk" dooz_prefix_r1 MINIANDROID_DUMMY=0
  run1 dooz_prefix_r2 "$CA/dooz_23_toplevel.apk" dooz_prefix_r2 MINIANDROID_DUMMY=0
  ;;
anchor)
  run_anchor 1
  run_anchor 2
  ;;
all)
  run1 dooz_prefix_r1 "$CA/dooz_23_toplevel.apk" dooz_prefix_r1 MINIANDROID_DUMMY=0
  run1 dooz_prefix_r2 "$CA/dooz_23_toplevel.apk" dooz_prefix_r2 MINIANDROID_DUMMY=0
  run_anchor 1
  run_anchor 2
  ;;
esac
