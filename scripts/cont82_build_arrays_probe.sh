#!/usr/bin/env bash
# cont81_build_f382_probe.sh — build the F-NEW-382 ART-identity regression
# probe with the real aapt2/ECJ/D8 chain (canonical recipe).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/cont82_arrays_fixture
OUT=run/cont82/cont82_arrays_probe.apk
WORK=tmp/cont82_arrays_build
rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "arrays probe: $(sha256sum "$OUT" | cut -c1-16)"
