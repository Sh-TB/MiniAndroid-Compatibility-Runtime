#!/usr/bin/env bash
# cont54_build_probe.sh — build the F-NEW-326 probe (the AOSP
# ViewGroup.getChildMeasureSpec law + the framework-boundary static
# resolution) with the real aapt2/ECJ/D8 toolchain.
#
# TWO variants from ONE source tree:
#   fnew326_probe.apk  — unpatched: every call's method_id owner is
#                        ViewGroup (direct framework-owner face).
#   fnew326b_probe.apk — byte-patched: the getChildMeasureSpec method_id
#                        class_idx is rewritten to MyBox (the support-lib
#                        R8 artifact shape — child-class-owned owner with
#                        NO declaration anywhere in the DEX; engine-only
#                        artifact, method_id sort order not re-sorted).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew326_probe
WORK=tmp/cont54_f326_build
OUT_A=run/cont54/fnew326_probe.apk
OUT_B=run/cont54/fnew326b_probe.apk
rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex" "$WORK/apk"

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen"

find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"

find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"

cp "$WORK/apk/resources.apk" "$OUT_A"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT_A" classes.dex )
echo "built $OUT_A: $(sha256sum "/home/z/my-project/$OUT_A" | cut -c1-16)"

# Patched variant: rewrite the getChildMeasureSpec method_id class_idx
# (ViewGroup -> MyBox) inside classes.dex, then re-zip.
python3 scripts/cont54_patch_method_id.py \
  "$WORK/dex/classes.dex" \
  "Landroid/view/ViewGroup;" "getChildMeasureSpec" \
  "Lcom/probe/f326/MyBox;"
cp "$WORK/apk/resources.apk" "$OUT_B"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT_B" classes.dex )
echo "built $OUT_B: $(sha256sum "/home/z/my-project/$OUT_B" | cut -c1-16)"
