#!/bin/bash
# cont19_seven_target_battery.sh — #383 amendment: audit the reported
# "7 FULLY_VERIFIED targets with no regression" at the CURRENT binary.
# Invocation = #382 §7 documented repro pattern (1080x1920, frames 5, 15s).
# Expected SHA16s: A103 transfer claims + evidence/cont15/sixgame_validation.json
# + cont18 anchor records. Output: run/cont19/battery/
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont19/battery
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apkpath> <want|none>
  local label="$1" apk="$2" want="${3:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local verdict="DRIFT"
  [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$want" = "none" ] && verdict="recorded"
  echo "BATTERY $label rc=$rc sha=$sha want=$want $verdict"
}

# ---- in-house six (expected = cont15 records == A103 claims, except snakeneon) ----
run1 g2048            "$BASE/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"          59ca1526611c4622
run1 tetris           "$BASE/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"       f360daa244cfca8d
run1 snake_deluxe     "$BASE/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"     34a712689ce66e58
run1 snakeneon        "$BASE/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk" 24fb7694eb64634a
run1 tictactoe_deluxe "$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk" af6094295ecb50e3
run1 minicraft        "$BASE/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk" b0876952f41e4af2
# ---- real-app anchors at this container's binary ----
run1 gmdice           "$BASE/upload/canonical_apks/de.duenndns.gmdice_8.apk"          f3b483fe7b7cf51b
run1 dooz             "$BASE/upload/canonical_apks/dooz_23_toplevel.apk"              d602648e8e401895

echo "--- run2/run3 for determinism (per target that matched or is contested) ---"
for t in g2048 tetris snake_deluxe snakeneon tictactoe_deluxe minicraft gmdice dooz; do
  case "$t" in
    g2048)            APK="$BASE/upload/s80_games/build_2048/g2048_v1.0_vc1.apk";; 
    tetris)           APK="$BASE/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk";;
    snake_deluxe)     APK="$BASE/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk";;
    snakeneon)        APK="$BASE/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk";;
    tictactoe_deluxe) APK="$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk";;
    minicraft)        APK="$BASE/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk";;
    gmdice)           APK="$BASE/upload/canonical_apks/de.duenndns.gmdice_8.apk";;
    dooz)             APK="$BASE/upload/canonical_apks/dooz_23_toplevel.apk";;
  esac
  run1 "${t}_r2" "$APK" none
  run1 "${t}_r3" "$APK" none
done
echo "BATTERY DONE"
