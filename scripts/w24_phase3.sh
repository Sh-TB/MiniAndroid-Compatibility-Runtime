#!/usr/bin/env bash
# w24_phase3.sh — decisive scheduler discriminators + PCH probe:
#   1. EXP-C PCH probe (alternating x2)
#   2. EXP-D Ninja build, flags EXACTLY matching Make FASTPROFILE
#      (incl. the missing -DMINIANDROID_HAVE_WEBP — parity finding)
#   3. EXP-B raw xargs -P2 build of the same 88 commands (no make)
#   4. diskstats I/O volume around the xargs build
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl
NINJA=/home/z/my-project/tools/dl/ninja-bin/ninja
CMAKE=/home/z/my-project/tools/dl/cmake-3.30.5-linux-x86_64/bin/cmake

# --- 1. PCH probe ---
bash /home/z/my-project/scripts/w24_probeC_pch.sh 2>&1 | grep -aE "PCH BUILD|PROBE|DONE" | tee $EV/RAW_LOGS/probeC_pch.txt

# --- 2. Ninja build (parity flags) ---
rm -rf build_w24ninja
$RUN --log $EV/RAW_LOGS/w24_ninja_j2.log --out $OUT \
  bash -c "$CMAKE -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS='-DMINIANDROID_HAVE_WEBP' -DCMAKE_CXX_FLAGS_RELEASE='-O2 -g1' -B build_w24ninja -S . > $EV/RAW_LOGS/w24_ninja_configure.txt 2>&1 && $NINJA -C build_w24ninja -j2 miniandroid"
sha256sum build_w24ninja/miniandroid 2>/dev/null | cut -c1-32 > $EV/RAW_LOGS/w24_ninja_sha.txt

# --- 3. raw xargs -P2 build (no make, no shell-per-recipe beyond xargs) ---
rm -rf build_w24x
grep -aE " -c -o " $EV/RAW_LOGS/w24_fastprofile_j1.log | sed 's/^ *[0-9.]* //; s|build_w24b1|build_w24x|' > /tmp/w24_cmds.txt
wc -l /tmp/w24x_cmds.txt > /dev/null 2>&1 || true
LINKCMD=$(grep -aE " -rdynamic " $EV/RAW_LOGS/w24_fastprofile_j1.log | head -1 | sed 's/^ *[0-9.]* //; s|build_w24b1|build_w24x|')
before=$(cat /proc/diskstats | awk '$3 ~ /(sda|vda|xvda|nvme)/ {print $6, $10}')
$RUN --log $EV/RAW_LOGS/w24_xargs_j2.log --out $OUT \
  bash -c "mkdir -p build_w24x && xargs -P2 -I{} sh -c {} < /tmp/w24_cmds.txt && $LINKCMD"
after=$(cat /proc/diskstats | awk '$3 ~ /(sda|vda|xvda|nvme)/ {print $6, $10}')
echo "diskstats before: $before" >> $EV/RAW_LOGS/w24_io_volume.txt
echo "diskstats after:  $after" >> $EV/RAW_LOGS/w24_io_volume.txt
echo PHASE3_DONE
