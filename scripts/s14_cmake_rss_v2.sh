#!/usr/bin/env bash
# S14-d v2 (AUD-52 close): peak RSS of a FULL BUILD_TESTS=ON build, measured
# with scripts/s14_time_wrapper.py (os.wait4 rusage = whole-tree per-process
# peak, same metric as GNU time -v; /usr/bin/time is absent in this sandbox).
# -j2 = the repo's canonical parallelism; the concurrent RSS sum is not
# observable by wait4 either (max-children semantics) — documented limitation,
# the metric stays comparable to the W22-C "-j1 1427MB" baseline record.
# Then the CTest battery on the same tree.
set -uo pipefail
cd /home/z/my-project/miniandroid
RSS_LOG=evidence/audit/RAW_LOGS/cmake_testbuild_rss_2026-11-20.log
CT_LOG=evidence/audit/RAW_LOGS/cmake_ctest_battery_2026-11-20.log
rm -rf build_tests
echo "== cmake BUILD_TESTS=ON configure v2 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" | tee "$RSS_LOG"
cmake -S . -B build_tests -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON 2>&1 | tee -a "$RSS_LOG"
cfg_rc=${PIPESTATUS[0]}
echo "== configure rc=$cfg_rc; timed -j2 build (s14_time_wrapper.py) ==" | tee -a "$RSS_LOG"
python3 /home/z/my-project/scripts/s14_time_wrapper.py cmake --build build_tests -j2 2>&1 | tee -a "$RSS_LOG"
grep -E "Maximum resident|Elapsed" "$RSS_LOG" > /tmp/s14_rss_lines_v2.txt || true
cat /tmp/s14_rss_lines_v2.txt | tee -a "$RSS_LOG"
ctest --test-dir build_tests --output-on-failure 2>&1 | tee "$CT_LOG"
ct_rc=${PIPESTATUS[0]}
echo "== ctest rc=$ct_rc ==" >> "$CT_LOG"
tail -4 "$CT_LOG"
echo "V2 FINAL: cfg_rc=$cfg_rc ctest_rc=$ct_rc"
