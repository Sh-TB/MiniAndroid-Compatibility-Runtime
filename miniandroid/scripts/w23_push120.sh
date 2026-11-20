#!/usr/bin/env bash
# w23_push120.sh — P120: push the 120 s production-build question with the
# remaining measured levers (no semantic weakening; production flags stay
# unchanged for the canonical profile).
#   R1  ccache COLD -j2 clean build  -> fills the cache, records cold -j2 wall + binary sha
#   R2  ccache WARM -j1 clean rebuild -> the 120 s-target claim: wall + BYTE-IDENTITY sha check
#   R3  -g1 -j2 clean build (measurement variant, NOT adopted)
#   R4  -j3 clean build (parallelism ceiling / RAM bound evidence, measurement only)
set -x
cd /home/z/my-project/miniandroid
CC=/home/z/my-project/tools/ccache-bin/ccache
export CCACHE_DIR=/home/z/my-project/tools/ccache_cache
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
EV=evidence/w23

rm -rf build_cc build_g1 build_j3

# R1: ccache cold, -j2 (cache fill + the cold -j2 ccache number)
$RUN --log $EV/p120_ccache_cold_j2.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j2 --output-sync all
echo "R1 rc=$? cold-j2 sha:" | tee $EV/p120_warm_sha_check.txt
sha256sum build_cc/miniandroid | cut -c1-32 | tee -a $EV/p120_warm_sha_check.txt
$CC -s > $EV/p120_ccache_stats_cold.txt 2>&1

# R2: ccache warm, -j1 (identical content, empty tree)
rm -rf build_cc
$RUN --log $EV/p120_ccache_warm_j1.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j1 --output-sync all
echo "R2 rc=$? warm-j1 sha:" | tee -a $EV/p120_warm_sha_check.txt
sha256sum build_cc/miniandroid | cut -c1-32 | tee -a $EV/p120_warm_sha_check.txt
$CC -s > $EV/p120_ccache_stats_warm.txt 2>&1
echo "IDENTITY_CHECK: $(grep -c a20ad3311f036771 $EV/p120_warm_sha_check.txt) of 2 shas match production a20ad3311f036771" | tee -a $EV/p120_warm_sha_check.txt
rm -rf build_cc "$CCACHE_DIR"

# R3: -g1 -j2 (measurement variant — debug-info compromise, NOT adopted)
$RUN --log $EV/p120_g1_j2.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_g1 CXXFLAGS="-std=c++17 -Wall -Wextra -O2 -MMD -MP -g1" -j2 --output-sync all
echo "R3 rc=$? g1-j2 sha:" | tee -a $EV/p120_warm_sha_check.txt
sha256sum build_g1/miniandroid | cut -c1-32 | tee -a $EV/p120_warm_sha_check.txt
rm -rf build_g1

# R4: -j3 (measurement — parallelism ceiling; OOM here = the documented RAM bound)
free -m >> $EV/p120_j3_mem.txt 2>&1
$RUN --log $EV/p120_j3.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_j3 -j3 --output-sync all
echo "R4 rc=$?" | tee -a $EV/p120_warm_sha_check.txt
rm -rf build_j3

echo P120_DONE | tee -a $EV/p120_warm_sha_check.txt
