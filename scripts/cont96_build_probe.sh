#!/usr/bin/env bash
# cont96_build_probe.sh — build the CONT-96 throughput probe (com.probe.perf1)
# with the real aapt2/ECJ/D8 toolchain.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont96_perf_probe
OUT=run/cont96/perf1.apk
WORK=tmp/cont96_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$WORK/flat" "$(dirname "$OUT")"
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/flat/res.zip" 2>/dev/null || mkdir -p "$FIX/res" && "$AAPT2" compile --dir "$FIX/res" -o "$WORK/flat/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$FIX/AndroidManifest.xml" \
  --java "$WORK/gen" "$WORK/flat/res.zip"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
