#!/usr/bin/env bash
# w24_phase4.sh — PART 4 combination measurement, alternating order (ABBA-ish):
#   BASE = FASTPROFILE=1            (W23-P2 fastprofile, no tiers)
#   CAND = FASTPROFILE=1 W24TIERS=1 (W24 candidate: measured -O1 tiers)
#   Sequence: BASE, CAND, CAND, BASE (fresh clean dir each; page-cache settle)
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl

build() { # $1=label $2=extra make vars
  rm -rf build_w24_$1
  sleep 3; sync
  $RUN --log $EV/RAW_LOGS/w24_combo_$1.log --out $OUT \
    make FASTPROFILE=1 $2 BUILDDIR=build_w24_$1 -j2 all
  sha256sum build_w24_$1/miniandroid 2>/dev/null | cut -c1-32 >> $EV/RAW_LOGS/w24_combo_shas.txt
}

build base_a ""
build cand_a "W24TIERS=1"
build cand_b "W24TIERS=1"
build base_b ""

echo PHASE4_DONE
