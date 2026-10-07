#!/bin/bash
# cont16_regression.sh — CONT-16 regression battery at the fix-batch binary.
# Anchors (recorded CONT-15 SHAs) x3 byte-identical, then probes/negatives/skill.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont16/reg
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)"

run3() { # run3 <pkg> <apkpath> <want-sha|none>
  local pkg="$1" apk="$2" want="${3:-none}"
  local store="$OUT/store_$pkg"
  [ -d "$store" ] || "$BIN" install "$apk" --data-root "$store" > /dev/null 2>&1
  for i in 1 2 3; do
    local o="$OUT/${pkg}_$i"; rm -rf "$o"; mkdir -p "$o"
    "$BIN" run --package "$pkg" --data-root "$store" --trace \
      --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
    local sha
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    if [ "$sha" = "$want" ]; then
      echo "ANCHOR $pkg run$i sha=$sha MATCH"
    else
      echo "ANCHOR $pkg run$i sha=$sha RECORDED=$want DRIFT"
    fi
  done
}

CA=$BASE/upload/canonical_apks
run3 io.github.yamin8000.dooz "$CA/dooz_23_toplevel.apk" d602648e8e401895
run3 dubrowgn.microtimer     "$CA/dubrowgn.microtimer_8.apk" da73010a37dd0189
run3 app.varlorg.unote       "$CA/app.varlorg.unote_30.apk"  4f1a9e4e8f64fae8
run3 de.duenndns.gmdice      "$CA/de.duenndns.gmdice_8.apk"  f3b483fe7b7cf51b
run3 com.darkempire78.opencalculator "$BASE/upload/opencalculator_53.apk" a976d2f9fb675cb3
run3 jp.sblo.pandora1.chess  "$BASE/upload/chess_jwtc_298.apk" b5a7a35d5fe0564b
echo "battery part 1 (anchors) done"
