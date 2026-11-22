#!/usr/bin/env bash
# s27_w3_wall.sh — S27-W3 gate: the 9-app regression wall + flip x3 on the
# PRODUCTION binary, with the CANONICAL per-app flags from the committed
# harness (scripts/p0_gate.sh W14/W16/W17 procedure + the apk-run Makefile
# convention SECS=120 frames=30 --trace). Hashes: sha256(screenshot.png)[:16]
# vs the S26-W1/S27-W2 canonical wall hashes.
set -u
cd /home/z/my-project/miniandroid
BIN=build/miniandroid
APK=/home/z/my-project/upload/handoff_apks
EV=evidence/s27
LOG=$EV/w3_wall.log

run_one() { # name apk maxsec frames extra...
  local name=$1 apk=$2 secs=$3 frames=$4; shift 4
  local dir=$EV/w3_$name
  rm -rf "$dir"; mkdir -p "$dir"
  MINIANDROID_VERSION_HEADER=build/generated/miniandroid_version.h \
    timeout 400 "$BIN" run --max-seconds "$secs" --frames "$frames" --trace \
    "$@" -o "$dir" --execution-mode real-dalvik "$APK/$apk" \
    > "$dir/stdout.log" 2> "$dir/stderr.log"
  echo $? > "$dir/rc.txt"
}

check() { # name expected
  local name=$1 expected=$2
  local dir=$EV/w3_$name
  local h rc verdict
  h=$(sha256sum "$dir/screenshot.png" 2>/dev/null | cut -c1-16)
  rc=$(cat "$dir/rc.txt" 2>/dev/null)
  verdict=$(grep -o 'verdict=[A-Z_]*' "$dir/stderr.log" | tail -1)
  if [ "$h" = "$expected" ]; then
    echo "[WALL-PASS] $name hash=$h rc=$rc $verdict" | tee -a "$LOG"
  else
    echo "[WALL-FAIL] $name hash=$h expected=$expected rc=$rc $verdict" | tee -a "$LOG"
  fi
}

echo "=== S27-W3 wall (canonical flags) $(date -u +%FT%TZ) ===" | tee -a "$LOG"

run_one np com.farmerbb.notepad_122.apk 90 30
check np 31ddd4d5b8e6d18e
run_one dice tech.gaskell.diceroller_1_debug.apk 120 30
check dice 0de952bf75f89409
run_one guess ru.zxalexis.ugaday_15.apk 120 30
check guess 87fe26766fc48d06
run_one ttt com.itsfrz.tictactoe_5.apk 120 30
check ttt d55056a8928a26ff
run_one pz name.livitski.games.puzzle.android_2.apk 200 50 --tap 197,112@25
check pz 6375a3a3813af176
run_one rnd com.minar.randomix_42.apk 120 30
check rnd 31ddd4d5b8e6d18e
run_one minos de.tcrass.minos_10004.apk 120 30
check minos b5a7a35d5fe0564b
run_one hw HelloWorldToast-1.4.0-android.apk 120 30
check hw acdd9f05dc9c7ece
run_one chess dk.cocode.chess_5022.apk 120 30
check chess d602648e8e401895

# flip x3 — the S27-W3 app: rc + REAL tree (ADOPT receipt) + deterministic
# NEW face (b270ff04 was the DEFAULT_BACKGROUND_ONLY blank; S27-W3 changes it
# on purpose — recorded as the new S27-W3 face).
for r in 1 2 3; do
  run_one flip_r$r org.ecos.logic.flip_a_coin_3.apk 120 30
  dir=$EV/w3_flip_r$r
  h=$(sha256sum "$dir/screenshot.png" 2>/dev/null | cut -c1-16)
  rc=$(cat "$dir/rc.txt" 2>/dev/null)
  v=$(grep -o 'verdict=[A-Z_]*' "$dir/stderr.log" | tail -1)
  a=$(grep -c 'S27-W3-ADOPT' "$dir/stderr.log")
  echo "[FLIP r$r] rc=$rc face=$h $v adopt=$a" | tee -a "$LOG"
done
h1=$(sha256sum "$EV/w3_flip_r1/screenshot.png" 2>/dev/null | cut -c1-16)
h2=$(sha256sum "$EV/w3_flip_r2/screenshot.png" 2>/dev/null | cut -c1-16)
h3=$(sha256sum "$EV/w3_flip_r3/screenshot.png" 2>/dev/null | cut -c1-16)
if [ "$h1" = "$h2" ] && [ "$h2" = "$h3" ]; then
  echo "FLIP DETERMINISM: PASS face=$h1 x3" | tee -a "$LOG"
else
  echo "FLIP DETERMINISM: FAIL $h1 $h2 $h3" | tee -a "$LOG"
fi
