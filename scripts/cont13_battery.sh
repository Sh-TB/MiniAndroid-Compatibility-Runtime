#!/usr/bin/env bash
# CONT-13 battery: F-NEW-518 binary — anchors (recorded SHAs must match)
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/cont13_battery
mkdir -p "$OUT"
run1() {
  local name=$1 pkg=$2 apk=$3 st=$4 secs=${5:-90} expect=${6:-}
  if [ ! -d "$st" ]; then "$B" install "$apk" --data-root "$st" > /dev/null 2>&1; fi
  local o="$OUT/${name}_r1"; rm -rf "$o"; mkdir -p "$o"
  "$B" run --package "$pkg" --data-root "$st" --trace --max-seconds "$secs" --frames 40 -o "$o" > "$o/stderr.log" 2>&1 || true
  local sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local unc=$(grep -cE 'EXC-UNCAUGHT' "$o/crash.log" 2>/dev/null || echo 0)
  local match=""
  [ -n "$expect" ] && { [ "$sha" = "$expect" ] && match="MATCH" || match="DRIFT"; }
  echo "$name: $sha uncaught=$unc $match"
}
run1 chess jwtc.android.chess /home/z/my-project/upload/chess_jwtc_298.apk "$OUT/store_chess" 90 a0319686
run1 opencalc com.darkempire78.opencalculator /home/z/my-project/upload/opencalculator_53.apk "$OUT/store_opencalc" 90 63020bc7
run1 microtimer dubrowgn.microtimer /home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk "$OUT/store_microtimer" 90 bbd350b6
run1 unote app.varlorg.unote /home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk "$OUT/store_unote" 90 7481e9b4
run1 tower3d stack.tower3d /home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk "$OUT/store_tower3d" 90 11a38a5a
