#!/usr/bin/env bash
# cont23_build_probe.sh — build the F-NEW-277 lifecycle-transaction probe APK
# with the canonical toolchain (tools/aapt2 + tools/ecj + tools/d8 + android-34),
# mirroring cont21_build_probes.sh's build_one().
set -euo pipefail
cd /home/z/my-project
AAPT2=tools/aapt2/aapt2
BOOT=tools/android-34/android-34.jar
ECJ=tools/ecj/ecj.jar
D8JAR=tools/d8/r8.jar

FIX=fixtures/lifecycle_transaction_probe
OUTAPK=upload/lifecycle_transaction_probe.apk
MAIN=$FIX/src/com/probe/lctx/MainActivity.java
WORK=tmp/probe_build/lifecycle_transaction_probe
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip" 2>/dev/null || true
if [ -f "$WORK/res.zip" ]; then
  "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
    --manifest "$FIX/AndroidManifest.xml" "$WORK/res.zip"
else
  "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
    --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
fi
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$MAIN"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUTAPK"
(cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUTAPK" classes.dex > /dev/null)
echo "built $OUTAPK: $(sha256sum "$OUTAPK" | cut -c1-16)"
