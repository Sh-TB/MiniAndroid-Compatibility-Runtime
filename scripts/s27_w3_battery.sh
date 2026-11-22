#!/usr/bin/env bash
# s26_law_loop.sh — S26-B gate: the 53-test law battery, per-test
# build→run→delete (the 5.4G disk budget cannot hold 53 test binaries at
# once — the S25-recorded constraint). Same run convention as the Makefile
# RUN_BATTERY macro (MINIANDROID_VERSION_HEADER + timeout).
set -u
cd /home/z/my-project/miniandroid
LOG=evidence/s27/w3_law_battery.log
: > "$LOG"
total=0; failed=0
TESTS=$(make -s print-TEST_LAW 2>/dev/null || sed -n '/^TEST_LAW = /,/^[A-Z_]* = /p' Makefile | head -n -1 | sed 's/^TEST_LAW = //; s/\\\\$//; s/\\\t*/ /g')
# Fallback extraction if print-TEST_LAW is not defined: pull the TEST_LAW block.
if [ -z "$TESTS" ] || [ "$TESTS" = "TEST_LAW" ]; then
  TESTS=$(awk '/^TEST_LAW = /{flag=1} flag{gsub(/\\\\/,""); line=$0; sub(/^TEST_LAW = /,"",line); gsub(/[[:space:]]+/, " ", line); printf "%s ", line; if ($0 !~ /\\\\$/) {exit}}' Makefile)
fi
for t in $TESTS; do
  [ -z "$t" ] && continue
  case "$t" in *=*) continue;; esac
  total=$((total+1))
  if ! make -s "build/tests/$t" > /dev/null 2>&1; then
    echo "[BUILD-FAIL] $t" | tee -a "$LOG"; failed=$((failed+1)); continue
  fi
  if MINIANDROID_VERSION_HEADER="build/generated/miniandroid_version.h" timeout 120 "./build/tests/$t" > "build/tests/$t.log" 2>&1; then
    echo "[PASS] $t" | tee -a "$LOG"
  else
    rc=$?; echo "[FAIL] $t (rc=$rc) — log: build/tests/$t.log" | tee -a "$LOG"; failed=$((failed+1))
  fi
  rm -f "build/tests/$t"
done
echo "LAW BATTERY SUMMARY: total=$total passed=$((total-failed)) failed=$failed" | tee -a "$LOG"
