#!/usr/bin/env bash
# w24_audit_probes.sh — B5/B6/B7 build-perf claims from #632, ABBA x2 order
# on the heaviest TU (src/renderer/ui_graphics.cpp per TU_COST_RANKING.csv).
set -u
cd /home/z/my-project/miniandroid
TU=src/dex/dalvik_bridge_domain_ui_graphics.cpp
OUT=evidence/audit/RAW_LOGS
mkdir -p $OUT
CXXFLAGS_BASE="-std=c++17 -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework"
run() { # $1=tag $2=extra flags
  local CMD=$(make -n FASTPROFILE=1 build/dex/dalvik_bridge_domain_ui_graphics.o 2>/dev/null | tail -1)
  CMD=${CMD/\-o build\/dex\/dalvik_bridge_domain_ui_graphics.o/-o /tmp/probe_$$.o}
  local t0=$(date +%s.%N)
  eval "$CMD" $2 >> $OUT/b567_probes.txt 2>&1
  local rc=$?
  local t1=$(date +%s.%N)
  echo "$1 rc=$rc $(echo "$t1 $t0" | awk '{printf "%.2fs", $1-$2}')" >> $OUT/b567_summary.txt
}
: > $OUT/b567_probes.txt; : > $OUT/b567_summary.txt
run A_baseline ""
run B_splitdwarf "-gsplit-dwarf"
run C_novta     "-fno-var-tracking-assignments"
run D_ggcmin    "--param ggc-min-expand=1 --param ggc-min-heapsize=8192"
run D_ggcmin    "--param ggc-min-expand=1 --param ggc-min-heapsize=8192"
run C_novta     "-fno-var-tracking-assignments"
run B_splitdwarf "-gsplit-dwarf"
run A_baseline ""
echo B567_PROBES_DONE >> $OUT/b567_summary.txt
rm -f /tmp/probe_$$.o; rm -f ui_graphics.o 2>/dev/null; ls *.o 2>/dev/null | head -2
