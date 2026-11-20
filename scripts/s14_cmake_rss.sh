#!/usr/bin/env bash
# S14-d (AUD-52 close): peak RSS of a FULL BUILD_TESTS=ON build, measured
# with GNU time (-j1 so the max-RSS-of-children number is the true per-
# process peak, comparable to the W22-C "-j1 572s/1427MB" baseline; the
# concurrent sum under -j2 is NOT observable with GNU time — documented
# limitation, not a gap). Then the CTest battery on the same tree.
set -uo pipefail
cd /home/z/my-project/miniandroid
RSS_LOG=evidence/audit/RAW_LOGS/cmake_testbuild_rss_2026-11-20.log
CT_LOG=evidence/audit/RAW_LOGS/cmake_ctest_battery_2026-11-20.log
echo "== cmake BUILD_TESTS=ON configure $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" | tee "$RSS_LOG"
cmake -S . -B build_tests -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON 2>&1 | tee -a "$RSS_LOG"
cfg_rc=${PIPESTATUS[0]}
echo "== configure rc=$cfg_rc; timed -j1 build ==" | tee -a "$RSS_LOG"
/usr/bin/time -v cmake --build build_tests -j1 2>&1 | tee -a "$RSS_LOG"
build_rc=${PIPESTATUS[0]}
echo "== build rc=$build_rc ==" | tee -a "$RSS_LOG"
grep -E "Maximum resident|Elapsed|Percent of CPU" "$RSS_LOG" | grep -E "Maximum resident|Elapsed|Percent of CPU" > /tmp/s14_rss_lines.txt || true
cat /tmp/s14_rss_lines.txt | tee -a "$RSS_LOG"
ctest --test-dir build_tests --output-on-failure 2>&1 | tee "$CT_LOG"
ct_rc=${PIPESTATUS[0]}
echo "== ctest rc=$ct_rc ==" >> "$CT_LOG"
tail -6 "$CT_LOG"
echo "FINAL: build_rc=$build_rc ctest_rc=$ct_rc"
