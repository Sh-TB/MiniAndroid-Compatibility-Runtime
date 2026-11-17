#!/usr/bin/env bash
# ISSUE-612 Phase 1: per-TU compile cost (pass A: -O0 -g0 frontend pass) + header fan-out
cd /home/z/my-project/miniandroid
mkdir -p evidence/issue612_audit
OUT=evidence/issue612_audit/tu_cost_passA.tsv
echo -e "tu\tseconds\tpeakMB" > $OUT
# discover the exact compile flags per object from the Makefile-generated deps
for cpp in $(find src -name "*.cpp" | sort); do
  obj="build/$(echo ${cpp#src/} | sed 's|\.cpp$|.o|; s|/|_|g')"
  # make the object dir
  mkdir -p "$(dirname $obj)"
  T=$( { /usr/bin/time -f "%e %M" g++ -std=c++17 -DMINIANDROID_HAVE_WEBP -DMINIANDROID_HAVE_LOTTIE -O0 -g0 -MMD -MP -c "$cpp" -o "$obj" ; } 2>&1 | tail -1 )
  S=$(echo $T | cut -d' ' -f1); M=$(echo $T | cut -d' ' -f2)
  echo -e "${cpp#src/}\t$S\t$((M/1024))" >> $OUT
  echo "done ${cpp#src/} ${S}s ${M}KB"
done
sort -t$'\t' -k2 -rn $OUT | head -12
