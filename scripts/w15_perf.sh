#!/bin/bash
cd /home/z/my-project/miniandroid
# 1) single-TU edit -> dev-so rebuild
touch src/dex/dalvik_engine_tail.cpp
T0=$(date +%s); make --no-print-directory dev-so -j1 > /dev/null 2>&1; T1=$(date +%s)
echo "PERF single-TU(devso): $((T1-T0))s"
# 2) shared-header edit -> dev-so cascade (dalvik_engine.h has 9 dex includers incl. bridge)
touch src/dex/dalvik_engine.h
T2=$(date +%s); make --no-print-directory dev-so -j1 > /dev/null 2>&1; T3=$(date +%s)
echo "PERF header-cascade(devso): $((T3-T2))s"
# 3) static relink only (no object changes): force relink via touch of a stable obj input? measure the dev-so relink component:
touch src/framework/android_shadows.cpp
T4=$(date +%s); make --no-print-directory dev-so -j1 > /dev/null 2>&1; T5=$(date +%s)
echo "PERF shadows-TU(devso): $((T5-T4))s"
# 4) static binary single-TU + relink
touch src/dex/dalvik_opcodes.cpp
T6=$(date +%s); make --no-print-directory all -j1 > /dev/null 2>&1; T7=$(date +%s)
echo "PERF single-TU(static+relink): $((T7-T6))s"
# 5) peak compiler RAM of the bridge TU (the C-02 constraint), /usr/bin/time
/usr/bin/time -v g++ -std=c++17 -Og -g0 -fPIC -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -DMINIANDROID_HAVE_WEBP -c src/dex/dalvik_bridge.cpp -o /tmp/w15_bridge_probe.o 2>&1 | grep -E "Maximum resident|Elapsed" | head -2
echo PERF_DONE
