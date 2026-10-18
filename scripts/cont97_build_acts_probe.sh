#!/usr/bin/env bash
# cont97_build_res_probe.sh — build the CONT-97 T3 resource probe
# (TextView.setText(@StringRes int) resolution law) with the real
# aapt2/ECJ/D8 toolchain. res/values/strings.xml linked via aapt2.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont97_acts_probe
MAN=$FIX/AndroidManifest.xml
OUT=run/cont97/acts2.apk
WORK=tmp/cont97_acts_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$WORK/flat" "$(dirname "$OUT")"
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/flat/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" \
  --java "$WORK/gen" "$WORK/flat/res.zip"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
