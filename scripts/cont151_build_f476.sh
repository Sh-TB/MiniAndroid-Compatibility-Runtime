#!/usr/bin/env bash
# cont151_build_f476.sh — build the F-NEW-476 invoke-arg-fidelity probe fixture
# (real aapt2/ECJ/D8 toolchain, same pattern as cont137_build_f474.sh).
set -euo pipefail
cd /home/z/my-project
FIX=miniandroid/tests/fixtures/fnew476_probe
WORK=tmp/cont151_f476_build
OUT=miniandroid/build/fixtures/fnew476_probe.apk
mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" miniandroid/build/fixtures

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml"
find "$FIX/src" -name "*.java" > "$WORK/msrc.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/msrc.txt"
find "$WORK/obj" -name "*.class" > "$WORK/mcls.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" \
  --output "$WORK/dex" @"$WORK/mcls.txt"
cp "$WORK/apk/resources.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
# show the invoke shapes in the dex for the record
python3 scripts/cont151_invoke_census.py "$OUT" 'Lcom/probe/fnew476/MainActivity$R;' 2>/dev/null || true
