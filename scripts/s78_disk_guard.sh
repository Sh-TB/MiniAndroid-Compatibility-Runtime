#!/usr/bin/env bash
# s78_disk_guard.sh — S78 §26 operational disk guard.
#
# S77 recorded a 100%-full disk that halted all development. This guard is
# the operational answer: check BEFORE any build; below threshold → STOP,
# report, and list SAFE cleanup candidates (regenerable/stale scratch only —
# canonical evidence is NEVER deleted).
#
# Usage: s78_disk_guard.sh [threshold_percent]   (default 85)
#   exit 0 = OK to build; exit 1 = STOP_BUILD.
THRESHOLD="${1:-85}"
AVAIL_KB=$(df --output=avail -k / | tail -1 | tr -d ' ')
TOTAL_KB=$(df --output=total -k / | tail -1 | tr -d ' ')
USED_PCT=$(df --output=pcent / | tail -1 | tr -d ' %')
AVAIL_MB=$((AVAIL_KB / 1024))
echo "[DISK-GUARD] total=$((TOTAL_KB/1048576))G avail=${AVAIL_MB}M used=${USED_PCT}% threshold=${THRESHOLD}%"

if [ "$USED_PCT" -ge "$THRESHOLD" ]; then
    echo "[DISK-GUARD] STOP_BUILD — used ${USED_PCT}% >= threshold ${THRESHOLD}%"
    echo "[DISK-GUARD] SAFE_CLEANUP_CANDIDATES (regenerable / stale scratch ONLY):"
    du -x -m /home/z/my-project/run 2>/dev/null | awk '$1>200 {printf "  %sMB %s (regenerable run outputs; keep run/s78_* + s77_baseline evidence)\n", $1, $2}'
    du -x -m /home/z/my-project/logs 2>/dev/null | awk '$1>100 {printf "  %sMB %s (old probe logs)\n", $1, $2}'
    ls -S /home/z/my-project/miniandroid/build/*.o 2>/dev/null | head -3 | sed 's/^/  stale object: /'
    echo "[DISK-GUARD] NEVER delete: docs/, docs/audit/, docs/evidence/, root_registry.json,"
    echo "[DISK-GUARD]   worklog.md, git history, reproducibility metadata (retention policy §27)."
    exit 1
fi
echo "[DISK-GUARD] OK — proceed"
exit 0
