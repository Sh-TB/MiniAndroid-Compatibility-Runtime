#!/usr/bin/env bash
# w24_phase5_next.sh — PART4 combo A/B (ABBA) + PART5 correctness on the W24
# candidate. Disk guard: only cand_a survives between builds. Gate runs on
# CANDIDATE codegen (dev tree rebuilt with FASTPROFILE=1 W24TIERS=1) and is
# compared against the canonical recorded hashes (evidence/w23).
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl
snap() { grep '^cpu ' /proc/stat | awk '{print $2+$4, $9}'; }

build() { # $1=label $2=make-flags $3=keep(0/1)
  rm -rf build_w24_$1; sleep 3; sync
  b=$(snap)
  $RUN --log $EV/RAW_LOGS/w24_combo_$1.log --out $OUT \
    make FASTPROFILE=1 $2 BUILDDIR=build_w24_$1 -j2 all
  a=$(snap)
  echo "$1 steal/user delta: $b -> $a" >> $EV/RAW_LOGS/w24_combo_steal.txt
  sha256sum build_w24_$1/miniandroid 2>/dev/null | cut -c1-32 >> $EV/RAW_LOGS/w24_combo_shas.txt
  [ "$3" = "0" ] && rm -rf build_w24_$1
  true
}
build base_a "" 0
build cand_a "W24TIERS=1" 1
build cand_b "W24TIERS=1" 0
build base_b "" 0

# disk guard before the dev-tree build (dev-so + tests need ~1.5G)
AV=$(df --output=avail -m /home | tail -1 | tr -d ' ')
if [ "$AV" -lt 1500 ]; then rm -rf build_fast build_p2b; fi

# PART5: 49-test battery on the kept candidate tree
$RUN --log $EV/RAW_LOGS/w24_cand_testall.log --out $OUT \
  make FASTPROFILE=1 W24TIERS=1 BUILDDIR=build_w24_cand_a test-all

# gate on CANDIDATE codegen: fresh dev tree at candidate flags
rm -rf build_dev_so build
$RUN --log $EV/RAW_LOGS/w24_cand_devso.log --out $OUT \
  make FASTPROFILE=1 W24TIERS=1 -j2 dev-so
bash scripts/p0_gate.sh /tmp/w24_gate | tee $EV/RAW_LOGS/w24_gate_hashes_cand.txt
python3 - <<'EOF'
import re
def parse(p):
    d = {}
    for l in open(p, errors="replace"):
        m = re.match(r"(\S+) sha=([0-9a-f]{16})", l)
        if m: d[m.group(1)] = m.group(2)
    return d
ref = parse("evidence/w23/gate_hashes_postsplit.txt")
got = parse("evidence/w24/RAW_LOGS/w24_gate_hashes_cand.txt")
bad = [k for k in ref if got.get(k) != ref[k]]
verdict = "MISMATCH %d: %s" % (len(bad), bad) if bad else "ALL-IDENTICAL (11/11)"
open("evidence/w24/RAW_LOGS/w24_gate_verdict.txt", "w").write(verdict + "\n")
print("GATE VERDICT:", verdict)
EOF

# incremental leaf edit on the candidate config
touch src/storage/data_root.cpp
$RUN --log $EV/RAW_LOGS/w24_final_incr_leaf.log --out $OUT \
  make FASTPROFILE=1 W24TIERS=1 BUILDDIR=build_w24_cand_a -j2 all
echo W24_PHASE5_DONE
