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
  # 4b. CONT-30W: package the fixture's root META-INF tree (if present) into
  # the APK. ServiceLoader discovers providers at the classpath root — for an
  # APK that is the APK's own ZIP entry table (META-INF/services/<Service>).
  # The CONT-7-era probe APKs carried this entry; the w4 rebuild lost it and
  # fnew252's SLPOS row silently regressed to hasNext=false (the engine's
  # apk-entry law then answered honest-empty, which is correct for a
  # provider-less APK). Fixture-driven and generic: any fixture shipping a
  # META-INF tree gets it packaged verbatim, no per-probe special case.
  if [ -d "$F/META-INF" ]; then
    (cd "$F" && zip -q -r "$O/${name}.apk" META-INF)
    r unzip -l "$O/${name}.apk" | rg "META-INF" || true
  fi
  # align+zipalign not needed for the runtime; sha20 identity print
  echo "BUILT $name -> $O/${name}.apk sha256_20=$(sha256sum "$O/${name}.apk" | cut -c1-20)"
}

build_probe fnew253_probe com.probe.fnew253
build_probe fnew252_probe com.probe.fnew252
build_probe cont7w3_probe com.probe.cont7w3
build_probe fnew289_probe com.probe.f289
build_probe fnew290_probe com.probe.f290
build_probe fnew291_probe com.probe.f291
build_probe fnew292_probe com.probe.f292
build_probe fnew293_probe com.probe.f293
build_probe fnew294_probe com.probe.f294
build_probe fnew295_probe com.probe.f295
build_probe fnew296_probe com.probe.f296
build_probe fnew297_probe com.probe.f297
echo "ALL PROBES BUILT"
