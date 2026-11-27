#!/usr/bin/env bash
# cleanup_run_battery.sh — run the already-built law battery exes directly
# (disk-safe: no rebuild; results logged), then free and do core+hostile.
set -u
cd /home/z/my-project/miniandroid
LOG=/home/z/my-project/scripts/cleanup_battery_run.log
: > "$LOG"
pass=0; fail=0; failed=""
for exe in build/tests/*_test build/tests/simple_test; do
  [ -x "$exe" ] || continue
  name=$(basename "$exe")
  if timeout 120 "$exe" > /tmp/one_test.log 2>&1; then
    echo "[PASS] $name" >> "$LOG"; pass=$((pass+1))
  else
    echo "[FAIL] $name rc=$?" >> "$LOG"; fail=$((fail+1)); failed="$failed $name"
  fi
done
echo "LAW BATCH SUMMARY: total=$((pass+fail)) passed=$pass failed=$fail" >> "$LOG"
echo "FAILED:$failed" >> "$LOG"
tail -3 "$LOG"
