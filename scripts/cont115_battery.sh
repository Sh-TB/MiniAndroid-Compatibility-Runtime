#!/usr/bin/env bash
# cont115_battery.sh — CONT-115 wave: the un-revalidated CONT-110 targets at current HEAD.
# New runtime evidence: sudoku (T02), whatsapp (T03), telegram 60s profile (T13-27/46/47),
# tower3d (T43/F-NEW-465), chess (T29), dooz anchor (T39-41), classifier selftest (T04).
set -u
cd /home/z/my-project
mkdir -p run/c115
LOG=run/c115/battery.log
: > "$LOG"
echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"
B=./miniandroid/build/miniandroid

run_one() { # name apk frames maxsec
  local name="$1" apk="$2" frames="$3" maxsec="$4"
  echo "== run $name (frames=$frames max=${maxsec}s) ==" | tee -a "$LOG"
  timeout $((maxsec*4+60)) "$B" run "$apk" --width 1080 --height 1920 --frames "$frames" \
    --max-seconds "$maxsec" -o "run/c115/$name" > /dev/null 2> "run/c115/$name.log"
  local rc=$?
  echo "rc=$rc" | tee -a "$LOG"
  if [ -f "run/c115/$name/screenshot.png" ]; then
    sha256sum "run/c115/$name/screenshot.png" | cut -c1-16 | tee -a "$LOG"
  else
    echo "NO_SCREENSHOT" | tee -a "$LOG"
  fi
  echo "uncaught=$(grep -c 'Uncaught\|uncaught' run/c115/$name.log 2>/dev/null || echo 0)" | tee -a "$LOG"
  echo "F100=$(grep -c 'F100-STATE' run/c115/$name.log 2>/dev/null || echo 0)" | tee -a "$LOG"
}

echo "== classifier selftest (T04) ==" | tee -a "$LOG"
timeout 120 python3 scripts/cont81_corpus_runner.py --selftest >> "$LOG" 2>&1
echo "selftest rc=$?" | tee -a "$LOG"

run_one sudoku  upload/sudoku_secuso_101.apk 5 30
run_one sudoku2 upload/sudoku_secuso_101.apk 5 30
run_one sudoku3 upload/sudoku_secuso_101.apk 5 30
run_one whatsapp upload/whatsapp.apk 5 30
run_one tower3d upload/canonical_apks/stack.tower3d_1.apk 5 30
run_one tower3d2 upload/canonical_apks/stack.tower3d_1.apk 5 30
run_one tower3d3 upload/canonical_apks/stack.tower3d_1.apk 5 30
run_one chess upload/chess_jwtc_298.apk 5 30
run_one chess2 upload/chess_jwtc_298.apk 5 30
run_one dooz upload/canonical_apks/io.github.yamin8000.dooz_23.apk 5 30

echo "== telegram 60s profile (T13-27/46/47) ==" | tee -a "$LOG"
timeout 400 "$B" run upload/telegram_official.apk --width 1080 --height 1920 --frames 5 \
  --max-seconds 60 -o run/c115/telegram > /dev/null 2> run/c115/telegram.log
echo "rc=$?" | tee -a "$LOG"
[ -f run/c115/telegram/screenshot.png ] && sha256sum run/c115/telegram/screenshot.png | cut -c1-16 | tee -a "$LOG" || echo NO_SCREENSHOT | tee -a "$LOG"
echo "uncaught=$(grep -c 'Uncaught\|uncaught' run/c115/telegram.log)" | tee -a "$LOG"
echo "F084=$(grep -c 'F084' run/c115/telegram.log)" | tee -a "$LOG"

echo "== dooz anchor compare ==" | tee -a "$LOG"
dsha=$(sha256sum run/c115/dooz/screenshot.png 2>/dev/null | cut -c1-16)
echo "dooz face=$dsha recorded=d602648e8e401895" | tee -a "$LOG"
if [ "$dsha" = "d602648e8e401895" ]; then echo "DOOZ_ANCHOR_MATCH" | tee -a "$LOG"; else echo "DOOZ_ANCHOR_DIFF" | tee -a "$LOG"; fi

echo "== key stderr lines ==" | tee -a "$LOG"
for f in sudoku whatsapp tower3d chess telegram; do
  echo "--- $f ---" | tee -a "$LOG"
  grep -E "verdict|first_missing|F100-STATE|PATH-LAW|mainActivity|draw_ops" "run/c115/$f.log" 2>/dev/null | head -6 | tee -a "$LOG"
done
echo "BATTERY_DONE" | tee -a "$LOG"
