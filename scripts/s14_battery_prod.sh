#!/usr/bin/env bash
# S14 (AUD-47/49 regression gate): production-profile battery 49/49 after
# the w15 7-vector E-05 extension + BUG-7 dedupe (src/dex/shadow_registry.h
# removed). build/ tree is warm from the previous session — only w15.cpp
# recompiles + its exe relinks.
set -uo pipefail
cd /home/z/my-project/miniandroid
LOG=evidence/audit/RAW_LOGS/s14_battery_after_dedupe_e05_2026-11-20.log
{
  echo "== S14 production battery $(date -u +%Y-%m-%dT%H:%M:%SZ) =="
  echo "tree state: w15_dalvik_lit_from16_law_test +4 const/high16 rows (13 total); src/dex/shadow_registry.h (BUG-7 stale 0-byte copy) REMOVED"
  make test-all 2>&1
  rc=$?
  echo "== make test-all rc=$rc =="
  exit $rc
} | tee "$LOG"
exit ${PIPESTATUS[0]}
