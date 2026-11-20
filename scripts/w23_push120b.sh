#!/usr/bin/env bash
# w23_push120b.sh — P120 retry: R1 (ccache cold -j2, cache fill) + R2 (ccache
# warm -j1 rebuild + BYTE-IDENTITY sha check). First attempt failed rc=127
# because a sandbox recycle wiped the gitignored tools/ccache-bin (BUG-2,
# fixed by re-downloading; the `test: Illegal number` line was the cosmetic
# symptom of $(CXX) -dumpfullversion returning empty).
set -x
cd /home/z/my-project/miniandroid
CC=/home/z/my-project/tools/ccache-bin/ccache
export CCACHE_DIR=/home/z/my-project/tools/ccache_cache
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
EV=evidence/w23

rm -rf build_cc "$CCACHE_DIR"

# R1b: ccache cold, -j2 (cache fill + cold -j2 ccache wall)
$RUN --log $EV/p120_ccache_cold_j2_retry.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j2 --output-sync all
echo "R1b rc=$? cold-j2 sha:" >> $EV/p120_warm_sha_check.txt
sha256sum build_cc/miniandroid | cut -c1-32 >> $EV/p120_warm_sha_check.txt
$CC -s > $EV/p120_ccache_stats_cold.txt 2>&1

# R2b: ccache warm, -j1 (identical content, empty tree)
rm -rf build_cc
$RUN --log $EV/p120_ccache_warm_j1_retry.log --out $EV/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j1 --output-sync all
echo "R2b rc=$? warm-j1 sha:" >> $EV/p120_warm_sha_check.txt
sha256sum build_cc/miniandroid | cut -c1-32 >> $EV/p120_warm_sha_check.txt
$CC -s > $EV/p120_ccache_stats_warm.txt 2>&1
echo "IDENTITY: $(grep -c a20ad3311f036771 $EV/p120_warm_sha_check.txt) of 2 match production a20ad3311f036771" >> $EV/p120_warm_sha_check.txt
rm -rf build_cc "$CCACHE_DIR"

echo P120B_DONE >> $EV/p120_warm_sha_check.txt
