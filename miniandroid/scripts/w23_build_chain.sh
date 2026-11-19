#!/usr/bin/env bash
# w23_build_chain.sh — W23-08 measurement chain (serial, disk-safe).
#   1. ccache cold full build (fills the W23 cache with post-split content)
#   2. ccache warm identical rebuild (the acceptance warm-rebuild number)
#   3. -g0-everywhere profile clean build (debug-info share of the clean build;
#      measurement variant, NOT adopted — production flags stay unchanged)
#   4. CMake configure + megabatch build (W23-05/06 parity + dup-source fix
#      validated at link level)
#   5. FINAL canonical post-split production clean build (the acceptance
#      production number; leaves build/ populated)
set -x
REPO=/home/z/my-project/miniandroid
cd "$REPO"
CC=/home/z/my-project/tools/ccache-bin/ccache
export CCACHE_DIR=/home/z/my-project/tools/ccache_cache
PY=python3
RUN="$PY /home/z/my-project/scripts/w22_build_run.py"

rm -rf build

# 1) ccache cold
$RUN --log evidence/w23/ccache_cold_w23.log --out evidence/w23/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j1 --output-sync all
$CC -s > evidence/w23/ccache_stats_cold.txt 2>&1

# 2) ccache warm (identical content, clean tree)
rm -rf build_cc
$RUN --log evidence/w23/ccache_warm_w23.log --out evidence/w23/build_bench.jsonl \
  make BUILDDIR=build_cc CXX="$CC g++" -j1 --output-sync all
$CC -s > evidence/w23/ccache_stats_warm.txt 2>&1
rm -rf build_cc "$CCACHE_DIR"

# 3) -g0 profile clean build (measurement variant)
rm -rf build
$RUN --log evidence/w23/prod_build_g0profile.log --out evidence/w23/build_bench.jsonl \
  make CXXFLAGS="-std=c++17 -Wall -Wextra -O2 -MMD -MP -g0" -j1 --output-sync all
rm -rf build

# 3b) -O1+g0 profile clean build (measurement variant: decomposition evidence
#     for the 120 s question — how much of the clean build is the -O2
#     optimization tier itself. NOT adopted.)
rm -rf build
$RUN --log evidence/w23/prod_build_o1g0profile.log --out evidence/w23/build_bench.jsonl \
  make CXXFLAGS="-std=c++17 -Wall -Wextra -O1 -MMD -MP -g0" -j1 --output-sync all
rm -rf build

# 4) CMake configure + megabatch (core lib compiles once; megabatch links
#    against it — validates the W23-06 dup-source removal at link level)
export PATH=/home/z/my-project/tools/dl/cmake-3.28.6-linux-x86_64/bin:$PATH
rm -rf build_cmake
cmake -S . -B build_cmake -DCMAKE_BUILD_TYPE=Release > evidence/w23/cmake_configure.log 2>&1
$RUN --log evidence/w23/cmake_megabatch_build.log --out evidence/w23/build_bench.jsonl \
  cmake --build build_cmake --target miniandroid_megabatch -j1
rm -rf build_cmake

# 5) FINAL canonical production clean build
$RUN --log evidence/w23/prod_build_final_w23.log --out evidence/w23/build_bench.jsonl \
  make -j1 --output-sync all
sha256sum build/miniandroid | cut -c1-32 > evidence/w23/final_binary_sha.txt
echo W23_BUILD_CHAIN_DONE
