#!/usr/bin/env bash
# cont95_battery.sh — full regression battery at binary aa9ade61b147c12b (F-NEW-397 SAX law).
set -u
cd /home/z/my-project
LOG=run/cont95/battery.log
: > "$LOG"
echo "== wall gate 4 rows x3 ==" | tee -a "$LOG"
for row in dooz opencalc unote microtimer; do
  bash scripts/cont70_gate.sh "$row" >> "$LOG" 2>&1
  tail -1 "$LOG" | tee -a "$LOG.sum" >/dev/null
done
rg "MATCH|CHANGED|FAIL" "$LOG" | tail -12
echo "== goldens ==" | tee -a "$LOG"
timeout 550 python3 scripts/user_golden_gate.py >> "$LOG" 2>&1
echo "goldens rc=$?"
echo "== negatives + reinstall ==" | tee -a "$LOG"
timeout 550 python3 scripts/s41_gatea_negative.py >> "$LOG" 2>&1
echo "gatea rc=$?"
echo "== MG-310 / MG-150 fences ==" | tee -a "$LOG"
timeout 300 python3 scripts/cont76_fence_mg310.py >> "$LOG" 2>&1
echo "mg310 rc=$?"
timeout 300 python3 scripts/cont76_fence_mg150.py >> "$LOG" 2>&1
echo "mg150 rc=$?"
echo "== selftests ==" | tee -a "$LOG"
timeout 300 python3 scripts/skill_selftest.py >> "$LOG" 2>&1
echo "selftest rc=$?"
echo "== F-NEW-376 fault battery ==" | tee -a "$LOG"
timeout 550 python3 scripts/cont73_fault_injection.py >> "$LOG" 2>&1
echo "f376 rc=$?"
echo "BATTERY DONE"
