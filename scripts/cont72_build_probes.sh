#!/usr/bin/env bash
# cont72_build_probes.sh — build the two issue-#364 review probes with the
# real aapt2/ECJ/D8 toolchain (gate_a_probe recipe). The priv probe is
# built twice: V1 (versionCode 1) and V2 (versionCode 2, V2 marker) for
# the install fault-injection update test.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() { # $1=fixture_dir $2=manifest $3=out_apk $4=workdir
  local FIX=$1 MAN=$2 OUT=$3 WORK=$4
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex"
  if [ -d "$FIX/res" ]; then
    "$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
    "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" \
      --java "$WORK/gen" --auto-add-overlay "$WORK/res.zip"
  else
    mkdir -p "$WORK/gen"
    "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
  fi
  find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

# ── Card 1 draw probe ──
build_one fixtures/cont72_draw_probe fixtures/cont72_draw_probe/AndroidManifest.xml \
  run/cont72/c72draw.apk tmp/cont72_build_draw

# ── Card 3 priv probe V1 ──
build_one fixtures/cont72_priv_probe fixtures/cont72_priv_probe/AndroidManifest.xml \
  run/cont72/c72priv_v1.apk tmp/cont72_build_priv_v1

# ── Card 3 priv probe V2 (same package, versionCode 2, V2 marker) ──
rm -rf tmp/cont72_priv_v2_fix
mkdir -p tmp/cont72_priv_v2_fix
cp -r fixtures/cont72_priv_probe/src tmp/cont72_priv_v2_fix/src
mkdir -p tmp/cont72_priv_v2_fix/src/com/probe/c72priv
sed 's/android:versionCode="1" android:versionName="1.0-v1marker"/android:versionCode="2" android:versionName="2.0-v2marker"/; s/android:label="C72PrivV1"/android:label="C72PrivV2"/' \
  fixtures/cont72_priv_probe/AndroidManifest.xml > tmp/cont72_priv_v2_manifest.xml
sed 's/public static final String VERSION = "V1"/public static final String VERSION = "V2"/' \
  fixtures/cont72_priv_probe/src/com/probe/c72priv/MainActivity.java \
  > tmp/cont72_priv_v2_fix/src/com/probe/c72priv/MainActivity.java
build_one tmp/cont72_priv_v2_fix tmp/cont72_priv_v2_manifest.xml \
  run/cont72/c72priv_v2.apk tmp/cont72_build_priv_v2
