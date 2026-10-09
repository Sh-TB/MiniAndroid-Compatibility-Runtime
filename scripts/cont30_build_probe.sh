#!/bin/bash
# CONT-30: build the F-NEW-286/287 synthetic probe (real toolchain:
# aapt2 compile+link, ECJ 1.8, D8 release — the canonical recipe).
set -e
export TOOLS=/tmp/my-project/tools
export PATH="$TOOLS:$PATH"
ROOT=/home/z/my-project
WORK=$ROOT/tmp/cont30_probebuild
mkdir -p "$WORK"
JAR=$TOOLS/android-34.jar
AAPT2=$TOOLS/aapt2/aapt2
ECJJAR=$TOOLS/ecj/ecj.jar
R8JAR=$TOOLS/d8/r8.jar
name=fnew286_probe
pkg=com.probe.f286
F=$ROOT/fixtures/$name
O=$WORK/$name
rm -rf "$O"; mkdir -p "$O/classes" "$O/dex"
$AAPT2 link -o "$O/${name}.apk" -I "$JAR" --manifest "$F/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJJAR" -1.8 -nowarn -cp "$JAR" -d "$O/classes" $(find "$F/src" -name '*.java')
java -cp "$R8JAR" com.android.tools.r8.D8 --release --lib "$JAR" --output "$O/dex" $(find "$O/classes" -name '*.class')
(cd "$O/dex" && zip -q -j "$O/${name}.apk" classes.dex)
echo "BUILT $name -> $O/${name}.apk sha256_20=$(sha256sum "$O/${name}.apk" | cut -c1-20)"
