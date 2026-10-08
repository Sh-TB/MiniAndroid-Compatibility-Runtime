#!/usr/bin/env bash
# cont21_build_probes.sh — rebuild the five DEX-behavior probe APKs at this
# container (run/w7, run/w8, run/cont18g were wiped with the container).
# Canonical toolchain: tools/aapt2 + tools/ecj + tools/d8 + android-34.
set -euo pipefail
cd /home/z/my-project
AAPT2=tools/aapt2/aapt2
BOOT=tools/android-34/android-34.jar
ECJ=tools/ecj/ecj.jar
D8JAR=tools/d8/r8.jar

build_one() { # fixture-dir out-apk main-src
  local FIX="$1" OUTAPK="$2" MAIN="$3"
  local WORK="tmp/probe_build/$(basename "$FIX")"
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
  "$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip" 2>/dev/null || true
  if [ -f "$WORK/res.zip" ]; then
    "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
      --manifest "$FIX/AndroidManifest.xml" "$WORK/res.zip"
  else
    "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
      --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
  fi
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$MAIN"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/apk/resources.apk" "$OUTAPK"
  (cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUTAPK" classes.dex > /dev/null)
  echo "built $OUTAPK: $(sha256sum "$OUTAPK" | cut -c1-16)"
}

mkdir -p run/w7 run/w8 run/cont18g
build_one fixtures/fcol_audit_probe       run/w7/fcol.apk        fixtures/fcol_audit_probe/src/com/probe/fcol/MainActivity.java
build_one fixtures/fnew259_probe          run/w7/f259.apk        fixtures/fnew259_probe/src/com/probe/f259/MainActivity.java
build_one fixtures/fnew259g_probe         run/w7/f259g.apk       fixtures/fnew259g_probe/src/com/probe/f259g/MainActivity.java
build_one fixtures/f266_probe             run/w8/f266.apk        fixtures/f266_probe/src/com/probe/f266/MainActivity.java
build_one fixtures/f268_exception_probe   run/cont18g/f268.apk   fixtures/f268_exception_probe/src/com/probe/f268/MainActivity.java
