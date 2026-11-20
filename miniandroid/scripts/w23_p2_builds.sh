#!/usr/bin/env bash
# w23_p2_builds.sh — P2: attribution + combined measurement
#   A: FASTPROFILE -j2 WITHOUT --output-sync (isolate the sync overhead)
#   B: FASTPROFILE + measured wave-7 inline-budget params on the probed
#      heavy TUs + no-sync (the P2 target build)
set -x
cd /home/z/my-project/miniandroid
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
EV=evidence/w23

rm -rf build_p2a build_p2b

# Build A: no-sync attribution
$RUN --log $EV/p2_fastprofile_j2_nosync.log --out $EV/build_bench.jsonl \
  make FASTPROFILE=1 BUILDDIR=build_p2a -j2 all
echo "A rc=$?" >> $EV/p2_results.txt
sha256sum build_p2a/miniandroid | cut -c1-32 >> $EV/p2_results.txt

# Build B: params (Makefile applies them under FASTPROFILE=1)
$RUN --log $EV/p2_fastprofile_params_j2.log --out $EV/build_bench.jsonl \
  make FASTPROFILE=1 BUILDDIR=build_p2b -j2 all
echo "B rc=$?" >> $EV/p2_results.txt
sha256sum build_p2b/miniandroid | cut -c1-32 >> $EV/p2_results.txt

echo P2_BUILDS_DONE >> $EV/p2_results.txt
