#!/bin/bash
# CONT-8 W4: rebuild the wave-3 synthetic probe APKs (fnew253/fnew252/cont7w3)
# real toolchain: aapt2 compile+link, ECJ 1.8, D8 release — same recipe as W3 re-proof
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
r() { echo "== $*"; "$@"; }

build_probe() {
  local name="$1" pkg="$2"
  local F=$ROOT/fixtures/$name
  local O=$WORK/$name
  rm -rf "$O"; mkdir -p "$O/classes" "$O/dex" "$O/res_out"
  # 1. aapt2 compile + link (res may be absent)
  if [ -d "$F/res" ]; then
    r "$AAPT2" compile --dir "$F/res" -o "$O/res.zip"
    r "$AAPT2" link -o "$O/${name}.apk" -I "$JAR" --manifest "$F/AndroidManifest.xml" \
      --java "$O/gen" "$O/res.zip" --auto-add-overlay
  else
    r "$AAPT2" link -o "$O/${name}.apk" -I "$JAR" --manifest "$F/AndroidManifest.xml" \
      --java "$O/gen" --auto-add-overlay
  fi
  # 2. ECJ compile
  local SRCS=$(find "$F/src" -name '*.java')
  r java -jar "$ECJJAR" -1.8 -nowarn -cp "$JAR" -d "$O/classes" $SRCS
  # 3. D8 dex
  r java -cp "$R8JAR" com.android.tools.r8.D8 --release \
    --lib "$JAR" --output "$O/dex" $(find "$O/classes" -name '*.class')
  # 4. package dex into APK (keep aapt2-produced entries: add classes.dex via zip)
  (cd "$O/dex" && zip -q -j "$O/${name}.apk" classes.dex)
  # align+zipalign not needed for the runtime; sha20 identity print
  echo "BUILT $name -> $O/${name}.apk sha256_20=$(sha256sum "$O/${name}.apk" | cut -c1-20)"
}

build_probe fnew253_probe com.probe.fnew253
build_probe fnew252_probe com.probe.fnew252
build_probe cont7w3_probe com.probe.cont7w3
echo "ALL PROBES BUILT"
