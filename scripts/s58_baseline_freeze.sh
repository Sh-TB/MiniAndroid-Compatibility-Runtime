#!/usr/bin/env bash
# s58_baseline_freeze.sh — S58 baseline freeze: run cont67_gate.sh rows, log verdicts.
# Usage: s58_baseline_freeze.sh <row> [<row> ...]
set -uo pipefail
BASE=/home/z/my-project
mkdir -p "$BASE/run/s58"
LOG=$BASE/run/s58/baseline.log
for row in "$@"; do
  echo "=== S58 FREEZE $row $(date -u +%H:%M:%S) ===" | tee -a "$LOG"
  bash "$BASE/scripts/cont67_gate.sh" "$row" 2>&1 | tee -a "$LOG"
done
echo "--- summary ---" | tee -a "$LOG"
grep -c "MATCH" "$LOG" | xargs -I{} echo "MATCH lines total: {}" | tee -a "$LOG"
