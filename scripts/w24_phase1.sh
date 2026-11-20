#!/usr/bin/env bash
# w24_phase1.sh — W24 PART 1: reproduce baselines sequentially (no contention).
#   A  canonical clean -j1            (production profile)
#   B  FASTPROFILE clean -j2          (current-tree fast baseline)
#   C  warm no-op rebuild             (same dir)
#   D  incremental leaf-source edit   (touch 1 small TU)
#   B1 FASTPROFILE clean -j1          (per-TU cost-ranking source)
#   E1 small common-header cascade    (dalvik_engine_types.h touch, -j1 per-TU data)
#   E2 big common-header cascade      (shadow_registry.h touch, -j2 wall number)
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
mkdir -p $EV/RAW_LOGS
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl

test -f src/storage/data_root.cpp
test -f src/dex/dalvik_engine_types.h
test -f src/dex/shadow_registry.h

# --- A ---
rm -rf build_w24a
$RUN --log $EV/RAW_LOGS/w24_canonical_j1.log --out $OUT make BUILDDIR=build_w24a -j1 all
sha256sum build_w24a/miniandroid | cut -c1-32 > $EV/RAW_LOGS/w24_canonical_j1_sha.txt
rm -rf build_w24a   # 2.3G disk budget: only the sha is kept

# --- B ---
rm -rf build_w24b
$RUN --log $EV/RAW_LOGS/w24_fastprofile_j2.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b -j2 all
sha256sum build_w24b/miniandroid | cut -c1-32 > $EV/RAW_LOGS/w24_fastprofile_j2_sha.txt

# --- C ---
$RUN --log $EV/RAW_LOGS/w24_warm_noop.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b -j2 all

# --- D ---
touch src/storage/data_root.cpp
$RUN --log $EV/RAW_LOGS/w24_incr_leaf.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b -j2 all

# --- B1 (per-TU ranking source, -j1 elapsed deltas = true per-TU durations) ---
rm -rf build_w24b1
$RUN --log $EV/RAW_LOGS/w24_fastprofile_j1.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b1 -j1 all

# --- E1 (small header cascade, -j1 so deltas are exact per-TU times) ---
touch src/dex/dalvik_engine_types.h
$RUN --log $EV/RAW_LOGS/w24_incr_header_small.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b1 -j1 all

# --- E2 (big header cascade, -j2 wall number) ---
touch src/dex/shadow_registry.h
$RUN --log $EV/RAW_LOGS/w24_incr_header_big.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b1 -j2 all

echo PHASE1_DONE
