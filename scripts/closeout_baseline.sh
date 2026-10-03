#!/usr/bin/env bash
# closeout_baseline.sh — re-establish ALL recorded gates at the rebuilt
# binary (b2b8c18bb92dab6a, HEAD 4347479d) before any closeout change.
# Evidence: run/closeout/baseline/*.log
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
BASE=/home/z/my-project
OUT=$BASE/run/closeout/baseline
mkdir -p "$OUT"
cd "$BASE"

echo "== binary sha16 =="
sha256sum "$B" | cut -c1-16

# 1. determinism anchors: install stores then run the gate
echo "== [1/8] determinism anchors =="
REG=$BASE/run/audit/regression
mkdir -p "$REG"
install_anchor() { # name pkg apk
  local st="$REG/store_$1"
  if [ ! -d "$st/data/app/$2" ]; then
    rm -rf "$st"; mkdir -p "$st"
    "$B" install "$3" --data-root "$st" >/dev/null 2>&1
  fi
}
install_anchor opencalc com.darkempire78.opencalculator "$BASE/upload/opencalculator_53.apk"
install_anchor chess jwtc.android.chess "$BASE/upload/chess_jwtc_298.apk"
install_anchor dooz io.github.yamin8000.dooz "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
install_anchor microtimer dubrowgn.microtimer "$BASE/upload/canonical_apks/dubrowgn.microtimer_8.apk"
install_anchor unote app.varlorg.unote "$BASE/upload/canonical_apks/app.varlorg.unote_30.apk"
bash scripts/working_vs_failing_probe.sh 2>&1 | tail -8

# 2. user goldens
echo "== [2/8] user goldens =="
python3 scripts/user_golden_gate.py 2>&1 | tail -8

# 3. loading probe
echo "== [3/8] loading probe =="
bash scripts/loading_probe_runner.sh 2>&1 | tail -5

# 4. gate A probe (canonical probe_store path the gates expect)
echo "== [4/8] gate A probe =="
rm -rf "$BASE/probe_store"; mkdir -p "$BASE/probe_store"
"$B" install gate_a_probe.apk --data-root "$BASE/probe_store" >/dev/null 2>&1
"$B" run --package com.probe.gatea --data-root "$BASE/probe_store" \
    -o "$OUT/gatea_run1" >/dev/null 2>&1
awk -F'|' '{print $3}' "$BASE/probe_store/data/data/com.probe.gatea/files/gate_a_results.jsonl" | sort | uniq -c

# 5. negatives
echo "== [5/8] negatives =="
mkdir -p run/gatea; cp gate_a_probe.apk run/gatea/gate_a_probe.apk
python3 scripts/s41_gatea_negative.py 2>&1 | tail -3

# 6. reinstall matrix
echo "== [6/8] reinstall matrix =="
python3 scripts/s41_gatea_reinstall.py 2>&1 | tail -3

# 7. uninstall proof
echo "== [7/8] uninstall proof =="
bash scripts/forensic_uninstall_proof.sh 2>&1 | tail -3

echo "== [8/8] done =="
