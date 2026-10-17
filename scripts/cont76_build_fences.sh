#!/usr/bin/env bash
# cont76_build_fences.sh — build the CONT-76 fence probes (MG-310 clinit
# ordering + MG-150 transform hit-test) with the real aapt2/ECJ/D8 chain.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() {
    local FIX=$1 MAN=$2 OUT=$3 WORK=$4 PKG=$5
    rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
    "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
    find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
    java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
    find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
    java -cp "$D8JAR" com.android.tools.r8.D8 --release \
      --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
    cp "$WORK/base.apk" "$OUT"
    ( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
    echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

build_one fixtures/mg310_clinit_fence \
          fixtures/mg310_clinit_fence/AndroidManifest.xml \
          run/cont76/mg310_fence.apk \
          tmp/cont76_mg310_build "com.probe.mg310"

build_one fixtures/mg150_hittest_fence \
          fixtures/mg150_hittest_fence/AndroidManifest.xml \
          run/cont76/mg150_fence.apk \
          tmp/cont76_mg150_build "com.probe.mg150"
