#!/bin/bash
# MG-011 verification chain: canonical FASTPROFILE build + full battery
set -x
cd /home/z/my-project/miniandroid
{
  echo "=== BUILD $(date -u +%H:%M:%S) ==="
  make FASTPROFILE=1 -j2 all 2>&1 | tail -20
  echo "BUILD_RC=$?"
  echo "=== TEST-ALL $(date -u +%H:%M:%S) ==="
  make FASTPROFILE=1 -j2 test-all 2>&1 | tail -30
  echo "TESTALL_RC=$?"
  echo "=== DONE $(date -u +%H:%M:%S) ==="
} > /home/z/my-project/evidence/audit_raw/mg011_build_testall.log 2>&1
