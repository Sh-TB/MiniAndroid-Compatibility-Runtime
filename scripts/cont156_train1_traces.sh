#!/bin/bash
# cont156_train1_traces.sh — F-NEW-481 trigger-chain live census on dooz v23.
# Runs: replay-leg methods (em1.g/ff.g/sc0.g layer callbacks; pz0.r1/i1/k1;
# oz0.7834) under METHOD-TRACE to pin which links execute and which are dead.
set -u
BIN=miniandroid/build/miniandroid
APK=upload/canonical_apks/io.github.yamin8000.dooz_23.apk
OUT=run/c156
mkdir -p "$OUT"

trace_one() {
  local label="$1" filter="$2"
  MINIANDROID_METHOD_TRACE="$filter" MINIANDROID_METHOD_TRACE_BUDGET=200000 \
    timeout 100 "$BIN" run "$APK" --width 1080 --height 1920 --frames 5 \
    --max-seconds 25 -o "$OUT/${label}_face" > "$OUT/${label}.log" 2>&1
  local rc=$?
  local hits
  hits=$(rg -c "^\[(METHOD-IN|METHOD-TR)" "$OUT/${label}.log" 2>/dev/null || echo 0)
  local rc_line face
  rc_line=$(rg -o "rc=[0-9-]+" "$OUT/${label}.log" | tail -1)
  face=$(rg -o "face[ =:]+[0-9a-f]{8,16}" "$OUT/${label}.log" | tail -1)
  echo "$label rc=$rc $rc_line $face trace_hits=$hits"
}

trace_one t1_em1g   'Lem1;|g'
trace_one t1_ffg    'Lff;|g'
trace_one t1_sc0g   'Lsc0;|g'
trace_one t1_pz0r1  'Lpz0;|r1'
trace_one t1_pz0i1  'Lpz0;|i1'
trace_one t1_oz7834 'Loz0;|7834'
