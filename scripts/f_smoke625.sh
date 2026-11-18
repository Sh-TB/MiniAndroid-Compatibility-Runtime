#!/bin/bash
# FINAL Phase 1 post-merge smoke at merged main 9dafaadd41f5 (worktree, fresh builds)
set -x
MERGE_SHA=$(python3 -c "import json;print(json.load(open('/tmp/f_merge625.json'))['sha'])")
cd /home/z/my-project && git fetch origin 2>&1 | tail -1
git -C /tmp/wt625 checkout --detach "$MERGE_SHA" 2>&1 | tail -1
git -C /tmp/wt625 rev-parse HEAD | cut -c1-12
cd /tmp/wt625/miniandroid
t0=$(date +%s); make --no-print-directory all -j1 > /tmp/f_smoke_prod.log 2>&1; rc=$?; t1=$(date +%s)
echo "PROD_BUILD rc=$rc wall=$((t1-t0))s"
make --no-print-directory test-core -j1 > /tmp/f_smoke_prodtest.log 2>&1; rc=$?
echo "PROD_TEST rc=$rc pass=$(grep -c '\[PASS\]' /tmp/f_smoke_prodtest.log)"
t0=$(date +%s); make --no-print-directory DALVIK_SPLIT=0 test-core -j1 > /tmp/f_smoke_mono.log 2>&1; rc=$?; t1=$(date +%s)
echo "MONOLITH_BUILD_TEST rc=$rc wall=$((t1-t0))s pass=$(grep -c '\[PASS\]' /tmp/f_smoke_mono.log)"
t0=$(date +%s); make --no-print-directory dev-so -j1 > /tmp/f_smoke_devso.log 2>&1; rc=$?; t1=$(date +%s)
echo "DEVSO_BUILD rc=$rc wall=$((t1-t0))s"
make --no-print-directory dev-so-test -j1 > /tmp/f_smoke_devtest.log 2>&1; rc=$?
echo "DEVSO_TEST rc=$rc pass=$(grep -c '\[PASS\]' /tmp/f_smoke_devtest.log)"
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 3 -o /tmp/f_smoke_guess \
  /home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk > /tmp/f_smoke_guess.log 2>&1; rc=$?
echo "GUESS_PARITY rc=$rc sha=$(sha256sum /tmp/f_smoke_guess/screenshot.png 2>/dev/null | cut -c1-24)"
echo "SMOKE625 DONE"
