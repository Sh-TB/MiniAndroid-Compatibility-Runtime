#!/usr/bin/env bash
# cont117_battery.sh — cluster E (tasks E-01..E-10): zero-drift bracket at HEAD 4dd923e3.
# E-01 selftest | E-02..05 wall anchors dooz/opencalc/unote/microtimer | E-06 chess+tower3d whites
# E-07 negatives | E-08 registry id-unique | E-09 registry mirror consistency | E-10 HEAD==origin/main
set -u
cd /home/z/my-project
mkdir -p run/c117
LOG=run/c117/battery.log
: > "$LOG"
B=./miniandroid/build/miniandroid

echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"
echo "head=$(git rev-parse HEAD)" | tee -a "$LOG"

run_one() { # name apk anchor
  local name="$1" apk="$2" anchor="$3"
  echo "== E: run $name ==" | tee -a "$LOG"
  timeout 240 "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds 30 -o "run/c117/$name" > /dev/null 2> "run/c117/$name.log"
  echo "rc=$?" | tee -a "$LOG"
  local face="NO_SCREENSHOT"
  [ -f "run/c117/$name/screenshot.png" ] && face=$(sha256sum "run/c117/$name/screenshot.png" | cut -c1-16)
  echo "face=$face recorded=$anchor" | tee -a "$LOG"
  if [ "$face" = "$anchor" ]; then echo "${name}_ANCHOR_MATCH" | tee -a "$LOG"; else echo "${name}_ANCHOR_DIFF" | tee -a "$LOG"; fi
}

echo "== E-01 selftest ==" | tee -a "$LOG"
timeout 300 python3 scripts/cont81_corpus_runner.py --selftest >> "$LOG" 2>&1
echo "selftest rc=$?" | tee -a "$LOG"
grep -E "PASS|FAIL" "$LOG" | tail -3 | tee -a "$LOG"

run_one dooz      upload/canonical_apks/io.github.yamin8000.dooz_23.apk d602648e8e401895   # E-02
run_one opencalc  upload/opencalculator_53.apk                          d5f3c7b5e9936ae6   # E-03
run_one unote     upload/canonical_apks/app.varlorg.unote_30.apk        90a67cc1ddda57b7   # E-04
run_one microtimer upload/canonical_apks/dubrowgn.microtimer_8.apk      bbd350b6c14fbd52   # E-05
run_one chess     upload/chess_jwtc_298.apk                             a0319686d56ff5c0   # E-06a
run_one tower3d   upload/canonical_apks/stack.tower3d_1.apk             11a38a5aeeff45a6   # E-06b

echo "== E-07 negatives ==" | tee -a "$LOG"
timeout 550 python3 scripts/s41_gatea_negative.py >> "$LOG" 2>&1
echo "negatives rc=$?" | tee -a "$LOG"

echo "== E-08 registry id-unique ==" | tee -a "$LOG"
python3 - <<'PY' | tee -a "$LOG"
import json
reg = json.load(open('canonical/root_cause_registry.json'))
roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
ids = [r['id'] for r in roots]
print(f"roots={len(ids)} unique={len(set(ids))} ID_UNIQUE={len(ids)==len(set(ids))}")
PY

echo "== E-09 registry main==mirror ==" | tee -a "$LOG"
if [ -f root_registry.json ]; then
  python3 -c "
import json
main=json.load(open('root_registry.json'))
mir=json.load(open('canonical/root_cause_registry.json'))
mi={r['id']:r for r in (main['roots'] if isinstance(main,dict) and 'roots' in main else main)}
mr={r['id']:r for r in (mir['roots'] if isinstance(mir,dict) and 'roots' in mir else mir)}
diff=[k for k in set(mi)|set(mr) if mi.get(k)!=mr.get(k)]
print('main_roots=',len(mi),' mirror_roots=',len(mr),' differing_ids=',len(diff))
print('mirror_identical=', len(diff)==0)" | tee -a "$LOG"
else
  echo "root_registry.json not present (recorded as-is)" | tee -a "$LOG"
fi

echo "== E-10 HEAD==origin/main ==" | tee -a "$LOG"
git fetch origin 2>/dev/null
l=$(git rev-parse HEAD); r=$(git rev-parse origin/main)
echo "local=$l remote=$r MATCH=$([ "$l" = "$r" ] && echo YES || echo NO)" | tee -a "$LOG"

echo "== SUMMARY ==" | tee -a "$LOG"
grep -cE "_ANCHOR_MATCH" "$LOG" | xargs echo "anchors_matched:"
grep -E "PASS.*13|13.*PASS" "$LOG" | tail -1
