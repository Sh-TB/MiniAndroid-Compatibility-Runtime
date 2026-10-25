#!/usr/bin/env bash
# cont28_w1_anchors.sh — CONT-28 W1 semantic-neutrality anchors at the
# F516-law binary (62ef48805a0522c5). Expected = W7-rebase pinned faces:
#   opencalc 63020bc7  chess a0319686  dooz 31ddd4d5
#   microtimer bbd350b6  unote 7481e9b4  tower3d 11a38a5a
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/cont28/anchors
mkdir -p "$OUT"
run_anchor() { # name apk pkg want
  local name=$1 apk=$2 pkg=$3 want=$4
  local st="$OUT/store_$name"
  if [ ! -d "$st" ]; then
    "$B" install "$apk" --data-root "$st" > /dev/null 2>&1
  fi
  local o="$OUT/${name}_run1"; rm -rf "$o"; mkdir -p "$o"
  "$B" run --package "$pkg" --data-root "$st" --max-seconds 90 --frames 40 -o "$o" > "$o/run.log" 2>&1 || true
  local s
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local v="DRIFT"; [ "$s" = "$want" ] && v="MATCH"
  echo "ANCHOR $name sha=$s want=$want $v"
}
run_anchor opencalc   /home/z/my-project/upload/opencalculator_53.apk                         com.darkempire78.opencalculator 63020bc7
run_anchor chess      /home/z/my-project/upload/chess_jwtc_298.apk                            jwtc.android.chess              a0319686
run_anchor dooz       /home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk io.github.yamin8000.dooz       851cc176
run_anchor microtimer /home/z/my-project/upload/canonical_apks/dubrowgn.microtimer_8.apk      dubrowgn.microtimer             bbd350b6
run_anchor unote      /home/z/my-project/upload/canonical_apks/app.varlorg.unote_30.apk       app.varlorg.unote               7481e9b4
run_anchor tower3d    /home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk            stack.tower3d                   11a38a5a
