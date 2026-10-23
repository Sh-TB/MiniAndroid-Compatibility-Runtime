#!/bin/bash
# cont11_verify_fixes.sh — verify the three recurring-root fixes on the
# census-affected titles (fresh runs over the existing census stores).
cd /home/z/my-project
BIN=miniandroid/build/miniandroid
OUT=run/cont11_verify
mkdir -p $OUT

declare -A PKGS=(
  [app.simple.peri_983.apk]=app.simple.peri
  [ac.stresa.uturn_22.apk]=ac.stresa.uturn
  [cc.skysparkle.sparkledns_10006.apk]=cc.skysparkle.sparkledns
  [org.connectbot_11101000.apk]=org.connectbot
  [app.floatdeck_8.apk]=app.floatdeck
  [com.bitmavrick.lumolight_35.apk]=com.bitmavrick.lumolight
  [com.ashkanrafiee.librecontactsbackup_32.apk]=com.ashkanrafiee.librecontactsbackup
  [com.nononsenseapps.notepad_72700.apk]=com.nononsenseapps.notepad
  [eu.faircode.netguard_2026080101.apk]=eu.faircode.netguard
)

for apk in "${!PKGS[@]}"; do
  pkg=${PKGS[$apk]}
  store=run/cont11_census/store_$apk
  run=$OUT/r_$apk
  rm -rf "$run"; mkdir -p "$run"
  timeout 130 "$BIN" run --package "$pkg" --data-root "$store" \
    --dump-view-tree --max-seconds 60 --frames 6 -o "$run" \
    > "$run/run.log" 2>&1
  verdict=$(grep -oE "verdict=[A-Z_]+" "$run/run.log" | head -1)
  uncaught=$(grep -oE "uncaught at caller [^ ]+" "$run/run.log" | tail -1)
  exc=$(grep "\[SYNTH-EXC\]" "$run/run.log" | tail -1 | grep -oE "L[a-zA-Z0-9/$_]+(Exception|Error);" | head -1)
  printf "%-46s rc=%-3s %-34s site=%-42s exc=%s\n" \
    "$apk" "$?" "${verdict:-none}" "${uncaught:--}" "${exc:--}"
done
