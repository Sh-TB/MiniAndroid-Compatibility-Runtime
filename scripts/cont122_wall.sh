#!/usr/bin/env bash
# cont122_wall.sh — CONT-120 zero-drift wall: 9 anchors + negatives + registry + HEAD.
# Anchors include all 8 recorded through CONT-118 plus klondike (CONT-119 era face).
# Judge: every anchor face byte-identical after the four engine changes
# (F368 reflective un-gate, FIX-D12 wrong-thread law, GLSurfaceView.getHolder,
# FIX-TTT guarded native load). One ANCHOR_DIFF = investigate honestly, never suppress.
set -u
cd /home/z/my-project
mkdir -p run/c122
LOG=run/c122/battery.log
: > "$LOG"
B=./miniandroid/build/miniandroid

echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"
echo "head=$(git rev-parse HEAD)" | tee -a "$LOG"

run_one() { # name apk anchor [maxsec]
  local name="$1" apk="$2" anchor="$3" ms="${4:-30}"
  echo "== run $name ==" | tee -a "$LOG"
  timeout $((ms*4+90)) "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds $ms -o "run/c122/$name" > /dev/null 2> "run/c122/$name.log"
  echo "rc=$?" | tee -a "$LOG"
  local face="NO_SCREENSHOT"
  [ -f "run/c122/$name/screenshot.png" ] && face=$(sha256sum "run/c122/$name/screenshot.png" | cut -c1-16)
  echo "face=$face recorded=$anchor" | tee -a "$LOG"
  if [ "$face" = "$anchor" ]; then echo "${name}_ANCHOR_MATCH" | tee -a "$LOG"; else echo "${name}_ANCHOR_DIFF" | tee -a "$LOG"; fi
}

echo "== E-01 selftest ==" | tee -a "$LOG"
timeout 300 python3 scripts/cont81_corpus_runner.py --selftest >> "$LOG" 2>&1
echo "selftest rc=$?" | tee -a "$LOG"
grep -E "PASS|FAIL" "$LOG" | tail -3 | tee -a "$LOG"

run_one dooz       upload/canonical_apks/io.github.yamin8000.dooz_23.apk   d602648e8e401895   # 1
run_one opencalc   upload/opencalculator_53.apk                            d5f3c7b5e9936ae6   # 2
run_one unote      upload/canonical_apks/app.varlorg.unote_30.apk          90a67cc1ddda57b7   # 3
run_one microtimer upload/canonical_apks/dubrowgn.microtimer_8.apk         bbd350b6c14fbd52   # 4
run_one chess      upload/chess_jwtc_298.apk                               a0319686d56ff5c0   # 5
run_one tower3d    upload/canonical_apks/stack.tower3d_1.apk               11a38a5aeeff45a6   # 6 (libgdx loads clean — guard must not break it)
run_one sudoku     upload/sudoku_secuso_101.apk                            be640e39e82901c9   # 7
run_one klondike   upload/klondike_veldsoft_3.apk                          31ddd4d5b8e6d18e   # 8
run_one telegram   upload/telegram_official.apk                            20ac8cbbbb692e63 60 # 9

echo "== negatives ==" | tee -a "$LOG"
timeout 550 python3 scripts/s41_gatea_negative.py >> "$LOG" 2>&1
echo "negatives rc=$?" | tee -a "$LOG"

echo "== registry id-unique + mirror consistency ==" | tee -a "$LOG"
python3 - <<'PY' | tee -a "$LOG"
import json
reg = json.load(open('canonical/root_cause_registry.json'))
roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
ids = [r['id'] for r in roots]
print(f"roots={len(ids)} unique={len(set(ids))} ID_UNIQUE={len(ids)==len(set(ids))}")
main = json.load(open('root_registry.json'))
mroots = main['roots'] if isinstance(main, dict) and 'roots' in main else main
mids = {r['id'] for r in mroots}
cids = {r['id'] for r in roots}
print(f"main={len(mids)} mirror={len(cids)} MAIN_EQ_MIRROR={mids==cids}")
PY

echo "== HEAD check ==" | tee -a "$LOG"
echo "HEAD=$(git rev-parse HEAD) ORIGIN=$(git rev-parse origin/main)" | tee -a "$LOG"

echo "== SUMMARY ==" | tee -a "$LOG"
grep -c "ANCHOR_MATCH" "$LOG" | xargs echo "anchor_matches:"
grep -c "ANCHOR_DIFF" "$LOG" | xargs echo "anchor_diffs:"
