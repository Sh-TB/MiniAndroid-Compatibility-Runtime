#!/usr/bin/env bash
# W9 verification battery: 511b+512 binary 06b9eb7b8209c3ed
# 1) anchors x1 (chess restored + no drift on the other 5)
# 2) survivalmanual + deskclock + alexcalc (the W8 pins)
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/w9
mkdir -p "$OUT"
run1() { # name pkg apk store seconds
  local name=$1 pkg=$2 apk=$3 st=$4 secs=${5:-90}
  if [ ! -d "$st" ]; then "$B" install "$apk" --data-root "$st" > /dev/null 2>&1; fi
  local o="$OUT/${name}_r1"; rm -rf "$o"; mkdir -p "$o"
  "$B" run --package "$pkg" --data-root "$st" --trace --max-seconds "$secs" --frames 40 -o "$o" > "$o/stderr.log" 2>&1 || true
  local sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local unc=$(grep -cE 'EXC-UNCAUGHT' "$o/crash.log" 2>/dev/null || echo 0)
  echo "$name: $sha uncaught=$unc"
}
# anchors (existing stores)
run1 chess jwtc.android.chess /home/z/my-project/upload/chess_jwtc_298.apk "$OUT/store_chess"
run1 opencalc com.darkempire78.opencalculator /home/z/my-project/upload/opencalculator_53.apk "$OUT/store_opencalc"
run1 microtimer dubrowgn.microtimer /home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk "$OUT/store_microtimer"
run1 unote app.varlorg.unote /home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk "$OUT/store_unote"
run1 tower3d stack.tower3d /home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk "$OUT/store_tower3d"
run1 dooz io.github.yamin8000.dooz /home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk "$OUT/store_dooz"
# W8 pins
run1 survivalmanual org.ligi.survivalmanual /home/z/my-project/upload/fdroid_batch/org.ligi.survivalmanual_500.apk "$OUT/store_survivalmanual"
run1 deskclock com.best.deskclock /home/z/my-project/upload/fdroid_batch/com.best.deskclock_2037.apk "$OUT/store_deskclock"
run1 alexcalc net.alexbarry.calc_android /home/z/my-project/upload/cont11_apks/alexcalc_20.apk "$OUT/store_alexcalc"
