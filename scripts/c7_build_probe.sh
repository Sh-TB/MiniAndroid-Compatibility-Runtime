#!/usr/bin/env bash
# c7_build_probe.sh — Coder-7's aapt2-link probe recipe (verbatim from
# #520 wave-1 comment 6641617281; TOOLS adapted to this host layout).
# Usage: bash scripts/c7_build_probe.sh <fixture_dir> <out.apk>
set -euo pipefail
REPO=/home/z/my-project; TOOLS=/home/z/my-project/tools
FIX=$1; OUT=$2; WORK=$(mktemp -d)
if [ -d "$FIX/res" ]; then
  "$TOOLS/aapt2/aapt2" compile --dir "$FIX/res" -o "$WORK/res.zip"
  "$TOOLS/aapt2/aapt2" link -o "$WORK/base.apk" -I "$TOOLS/android-34.jar" \
    --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen" --auto-add-overlay "$WORK/res.zip"
else
  mkdir -p "$WORK/gen"
  "$TOOLS/aapt2/aapt2" link -o "$WORK/base.apk" -I "$TOOLS/android-34.jar" \
    --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen"
fi
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$TOOLS/ecj/ecj.jar" -1.8 -nowarn -d "$WORK/obj" -cp "$TOOLS/android-34.jar" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"; mkdir -p "$WORK/dex"
java -cp "$TOOLS/d8/r8.jar" com.android.tools.r8.D8 --release \
  --lib "$TOOLS/android-34.jar" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"; ( cd "$WORK/dex" && zip -j -q -X "$OUT" classes.dex )
sha256sum "$OUT"
