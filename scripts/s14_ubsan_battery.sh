#!/usr/bin/env bash
# S14-c full phase (AUD-47 close): the ENTIRE 49-test battery built AND run
# under `make UBSAN=1` (-fsanitize=undefined -fno-sanitize-recover=all) —
# the superset of the #627 hub's "UBSan run 7/7" claim. Any latent UB in
# core code reached by the battery aborts with a nonzero exit.
set -uo pipefail
cd /home/z/my-project/miniandroid
LOG=evidence/audit/RAW_LOGS/s14_ubsan_battery_2026-11-20.log
{
  echo "== S14 UBSAN battery $(date -u +%Y-%m-%dT%H:%M:%SZ) =="
  echo "profile: UBSAN=1 -> -O1 -g1 -fsanitize=undefined -fno-sanitize-recover=all, tree build_ubsan/ (-g1: line tables only — full -g DWARF ENOSPC'd the 4.6G disk on the first attempt at test #23 link; -g1 does not affect codegen or sanitizer semantics)"
  make UBSAN=1 ubsan-e05 2>&1
  echo "== ubsan-e05 rc=$? =="
  make UBSAN=1 test-all 2>&1
  echo "== make UBSAN=1 test-all rc=$? =="
} | tee "$LOG"
exit ${PIPESTATUS[0]}
