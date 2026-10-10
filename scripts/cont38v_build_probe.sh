#!/bin/bash
# cont38v_build_probe.sh — build the CONT-38v independent-verification probe
# (classkey_probe: Class-token map-key identity + full ListIterator contract)
# Same real-toolchain recipe as w4_build_probes.sh (aapt2 + ECJ 1.8 + D8).
set -e
export TOOLS=/tmp/my-project/tools
export PATH="$TOOLS:$PATH"
ROOT=/home/z/my-project
WORK=$ROOT/tmp/w4_probebuild
mkdir -p "$WORK"
JAR=$TOOLS/android-34.jar
AAPT2=$TOOLS/aapt2/aapt2
ECJJAR=$TOOLS/ecj/ecj.jar
R8JAR=$TOOLS/d8/r8.jar

build_probe() {
  local name="$1" pkg="$2"
  local F=$ROOT/fixtures/$name
  local O=$WORK/$name
  rm -rf "$O"; mkdir -p "$O/classes" "$O/dex" "$O/res_out"
  if [ -d "$F/res" ]; then
    "$AAPT2" compile --dir "$F/res" -o "$O/res.zip"
    "$AAPT2" link -o "$O/${name}.apk" -I "$JAR" --manifest "$F/AndroidManifest.xml" \
      --java "$O/gen" "$O/res.zip" --auto-add-overlay
  else
    "$AAPT2" link -o "$O/${name}.apk" -I "$JAR" --manifest "$F/AndroidManifest.xml" \
      --java "$O/gen" --auto-add-overlay
  fi
  local SRCS=$(find "$F/src" -name '*.java')
  java -jar "$ECJJAR" -1.8 -nowarn -cp "$JAR" -d "$O/classes" $SRCS
  java -cp "$R8JAR" com.android.tools.r8.D8 --release \
    --lib "$JAR" --output "$O/dex" $(find "$O/classes" -name '*.class')
  (cd "$O/dex" && zip -q -j "$O/${name}.apk" classes.dex)
  echo "BUILT $name -> $O/${name}.apk sha256_20=$(sha256sum "$O/${name}.apk" | cut -c1-20)"
}

build_probe classkey_probe com.probe.ckey
