#!/usr/bin/env bash
# S14 heavy chain: cmake RSS measurement (AUD-52) then full UBSan battery
# (AUD-47). build_tests is deleted between the phases so the two ~2GB
# trees never coexist (disk: 4.6G free).
set -uo pipefail
cd /home/z/my-project/miniandroid
bash /home/z/my-project/scripts/s14_cmake_rss.sh
rc_cmake=$?
rm -rf build_tests
bash /home/z/my-project/scripts/s14_ubsan_battery.sh
rc_ub=$?
rm -rf build_ubsan
echo "CHAIN FINAL: cmake_rc=$rc_cmake ubsan_rc=$rc_ub"
