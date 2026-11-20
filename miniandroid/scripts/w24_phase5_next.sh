#!/usr/bin/env bash
# w24_phase5_next.sh — run THIS FIRST in the next session (no re-derivation):
# PART4 combo A/B (ABBA) + PART5 correctness on the W24 candidate.
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl
build() { rm -rf build_w24_$1; sleep 3; sync; \
  $RUN --log $EV/RAW_LOGS/w24_combo_$1.log --out $OUT make FASTPROFILE=1 $2 BUILDDIR=build_w24_$1 -j2 all; \
  sha256sum build_w24_$1/miniandroid 2>/dev/null | cut -c1-32 >> $EV/RAW_LOGS/w24_combo_shas.txt; }
build base_a ""
build cand_a "W24TIERS=1"
build cand_b "W24TIERS=1"
build base_b ""
# correctness on the candidate tree
$RUN --log $EV/RAW_LOGS/w24_cand_testall.log --out $OUT make FASTPROFILE=1 W24TIERS=1 BUILDDIR=build_w24_cand_a test-all
bash scripts/p0_gate.sh /tmp/w24_gate >> $EV/RAW_LOGS/w24_gate.log 2>&1
# incremental on final config
touch src/storage/data_root.cpp
$RUN --log $EV/RAW_LOGS/w24_final_incr_leaf.log --out $OUT make FASTPROFILE=1 W24TIERS=1 BUILDDIR=build_w24_cand_a -j2 all
echo W24_PHASE5_DONE
