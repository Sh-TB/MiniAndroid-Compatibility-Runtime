#!/usr/bin/env bash
# P0 evidence: per-TU peak RSS + wall time on the EXACT production command
# (-O2 -g0, serial), plus -ftime-report capture per TU.
set -u
FLAGS='-std=c++17 -Wall -Wextra -g -O2 -MMD -MP -DMINIANDROID_HAVE_WEBP -g0'
INC='-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include'
mkdir -p evidence/p0_split
: > evidence/p0_split/per_tu_rss.txt
for f in dalvik_bridge dalvik_bridge_domain_jdk dalvik_bridge_domain_android_core \
         dalvik_bridge_domain_ui_graphics dalvik_bridge_domain_app_runtime \
         dalvik_bridge_domain_io_lang; do
  /usr/bin/time -v g++ $FLAGS $INC -c -o /tmp/p0_${f}.o src/dex/${f}.cpp \
    2> /tmp/p0_time_${f}.txt
  rss=$(grep -F 'Maximum resident' /tmp/p0_time_${f}.txt | awk '{print $6}')
  wall=$(grep 'Elapsed \(wall' /tmp/p0_time_${f}.txt | awk '{print $8}')
  printf '%-42s RSS=%8s KB  wall=%s\n' "$f" "$rss" "$wall" \
    | tee -a evidence/p0_split/per_tu_rss.txt
done
echo '--- -ftime-report (per TU, phases only) ---'
: > evidence/p0_split/ftime_report.txt
for f in dalvik_bridge_domain_jdk dalvik_bridge_domain_ui_graphics; do
  echo "=== $f ===" >> evidence/p0_split/ftime_report.txt
  g++ $FLAGS -ftime-report $INC -c -o /tmp/p0_ft_${f}.o src/dex/${f}.cpp 2>&1 \
    | grep -E "phase|TOTAL" | head -24 >> evidence/p0_split/ftime_report.txt
done
echo done
