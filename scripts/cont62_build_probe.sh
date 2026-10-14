#!/usr/bin/env bash
# cont62_build_probe.sh — build fixtures/fnew345_probe into run/cont62/f345.apk
# (real aapt2/ECJ/D8 toolchain, same harness as CONT-10's fnew259 probe;
#  renamed from the colliding scripts/cont11_build_probe.sh after the rebase
#  onto the remote line's own cont11 script — F-NEW-264 is taken upstream,
#  this root is F-NEW-345.)
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew345_probe
WORK=tmp/f345_build
OUT=run/cont62
mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" "$OUT"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$FIX/src/com/probe/f345/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/f345.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/f345.apk" classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/$OUT/f345.apk | cut -c1-16)"
