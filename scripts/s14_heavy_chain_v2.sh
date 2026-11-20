#!/usr/bin/env bash
# S14 heavy chain v2: strict tree isolation so the ~2GB build trees never
# coexist on the 4.6G disk (first attempt ENOSPC'd). Order:
#   1. delete build/ (production battery 49/49 evidence already committed in
#      RAW_LOGS; the tree is regenerable)
#   2. cmake v2 RSS phase (build_tests)  -> rm build_tests
#   3. UBSan battery phase (build_ubsan) -> rm build_ubsan
set -uo pipefail
cd /home/z/my-project/miniandroid
rm -rf build build_tests build_ubsan
bash /home/z/my-project/scripts/s14_cmake_rss_v2.sh
rc_cmake=$?
rm -rf build_tests
bash /home/z/my-project/scripts/s14_ubsan_battery.sh
rc_ub=$?
rm -rf build_ubsan
echo "CHAIN2 FINAL: cmake_rc=$rc_cmake ubsan_rc=$rc_ub"
