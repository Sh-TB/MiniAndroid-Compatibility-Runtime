#!/usr/bin/env bash
# w24_phase2.sh — sequential probe/measure chain (no CPU contention):
#   1. E2 fixed: REAL shadow_registry.h (src/framework/) cascade at -j2
#   2. BUG-7 check: is src/dex/shadow_registry.h a dead duplicate?
#   3. EXP-A probes (ABBA): heavy cold TUs + small tail at -O1 vs -O2
#   4. EXP-C: -E real per-header parse cost (top-12 headers)
#   5. PART2: -ftime-report phase costs (top-12 + 4 small TUs)
#   6. LPT scheduling model
set -x
cd /home/z/my-project/miniandroid
EV=evidence/w24
RUN="python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=$EV/build_bench.jsonl

# --- 1. E2 fixed ---
diff -q src/dex/shadow_registry.h src/framework/shadow_registry.h > $EV/RAW_LOGS/bug7_shadow_registry_dupes.txt 2>&1 || true
touch src/framework/shadow_registry.h
$RUN --log $EV/RAW_LOGS/w24_incr_header_big_fixed.log --out $OUT make FASTPROFILE=1 BUILDDIR=build_w24b1 -j2 all

# --- 3a. heavy cold -O1 probes ---
bash /home/z/my-project/scripts/w24_probeA_o1.sh 2>&1 | grep -E "^PROBE|DONE" | tee $EV/RAW_LOGS/probeA_o1_heavy.txt
# --- 3b. small tail -O1 probes ---
bash /home/z/my-project/scripts/w24_probeB_o1small.sh 2>&1 | grep -E "^PROBE|DONE" | tee $EV/RAW_LOGS/probeB_o1_small.txt

# --- 4. real per-header parse cost (-E) ---
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"
echo "header,n_consumers,preprocess_only_s" > $EV/HEADER_PARSE_COST.csv
for h in third_party/nlohmann_json/include/nlohmann/json.hpp \
         src/resources/res_config.h src/resources/res_id.h \
         src/resources/arsc_parser.h src/renderer/software_renderer.h \
         src/framework/adapter_scrap_bin.h src/apk/apk_parser.h \
         src/framework/android_shadows.h src/resources/attribute_set_store.h \
         src/dex/dex_parser.h src/dex/class_resolver.h \
         src/api/android_stubs.h src/dex/dalvik_engine_types.h; do
  test -f $h || continue
  { time g++ -std=c++17 -w -O2 -g1 -DMINIANDROID_HAVE_WEBP $INC -E -o /dev/null $h ; } 2> /tmp/w24hp.txt
  n=$(python3 /home/z/my-project/scripts/w24_hdr_consumers.py "$h")
  echo "$h,$n,$(grep -a real /tmp/w24hp.txt | awk '{print $2}')" >> $EV/HEADER_PARSE_COST.csv
done

# --- 5. phase costs ---
bash /home/z/my-project/scripts/w24_phase_costs.sh 2>&1 | tail -2

# --- 6. LPT model ---
python3 /home/z/my-project/scripts/w24_lpt_model.py | tee $EV/RAW_LOGS/lpt_model.txt

echo PHASE2_DONE
