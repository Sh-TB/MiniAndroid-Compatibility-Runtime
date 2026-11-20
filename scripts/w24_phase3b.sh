#!/usr/bin/env bash
# w24_phase3b.sh — fixed reruns: PCH probe (correct header paths), Ninja
# (explicit CMAKE_MAKE_PROGRAM), -ftime-report phase costs (fixed sed),
# steal-time sampling around one measurement.
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl
NINJA=/home/z/my-project/tools/dl/ninja-bin/ninja
CMAKE=/home/z/my-project/tools/dl/cmake-3.30.5-linux-x86_64/bin/cmake

# steal sampler around the Ninja build
snap() { grep '^cpu ' /proc/stat | awk '{print $2+$4, $9}'; }
b=$(snap)

# --- Ninja build (parity flags + explicit make program) ---
rm -rf build_w24ninja
$RUN --log $EV/RAW_LOGS/w24_ninja_j2b.log --out $OUT \
  bash -c "$CMAKE -G Ninja -DCMAKE_MAKE_PROGRAM=$NINJA -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS='-DMINIANDROID_HAVE_WEBP' -DCMAKE_CXX_FLAGS_RELEASE='-O2 -g1' -B build_w24ninja -S . > $EV/RAW_LOGS/w24_ninja_configure2.txt 2>&1 && $NINJA -C build_w24ninja -j2 miniandroid"
a=$(snap)
echo "steal/user delta during ninja build: $b -> $a" >> $EV/RAW_LOGS/w24_steal_sample.txt
sha256sum build_w24ninja/miniandroid 2>/dev/null | cut -c1-32 > $EV/RAW_LOGS/w24_ninja_sha.txt

# --- PCH probe fixed ---
sed -i 's|"src/resources/|"resources/|; s|"src/framework/|"framework/|; s|"src/renderer/|"renderer/|; s|"src/apk/|"apk/|; s|"src/storage/|"storage/|; s|"src/dex/|"dex/|; s|"src/api/|"api/|' /home/z/my-project/scripts/w24_probeC_pch.sh
bash /home/z/my-project/scripts/w24_probeC_pch.sh 2>&1 | grep -aE "PCH BUILD|PROBE|DONE" | tee $EV/RAW_LOGS/probeC_pch_fixed.txt

# --- phase costs (fixed sed) ---
bash /home/z/my-project/scripts/w24_phase_costs.sh 2>&1 | tail -2
echo PHASE3B_DONE
