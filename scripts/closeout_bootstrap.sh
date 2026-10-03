#!/usr/bin/env bash
# Closeout bootstrap: build toolchain + APK re-fetch (container was reset).
set -u
BASE=/home/z/my-project
TC=$BASE/tools/toolchain
mkdir -p "$TC" "$BASE/tmp/closeout_apks"
cd "$TC"

echo "== 1. aapt2 =="
if [ ! -x aapt2 ]; then
  curl -sSL -o aapt2.zip https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.3.2-10880808/aapt2-8.3.2-10880808-linux.jar
  unzip -o -q aapt2.zip aapt2 && rm aapt2.zip && chmod +x aapt2
fi
./aapt2 version 2>&1

echo "== 2. ecj =="
[ -f ecj.jar ] || curl -sSL -o ecj.jar https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/3.36.0/ecj-3.36.0.jar
ls -la ecj.jar

echo "== 3. r8 =="
[ -f r8.jar ] || curl -sSL -o r8.jar https://storage.googleapis.com/r8-releases/raw/8.3.37/r8.jar
ls -la r8.jar

echo "== 4. android-34 stubs =="
[ -f android-34.jar ] || curl -sSL -o android-34.jar https://raw.githubusercontent.com/Sable/android-platforms/master/android-34/android.jar
ls -la android-34.jar

echo "== 5. APK fetch (F-Droid) =="
cd "$BASE/tmp/closeout_apks"
fetch() { # name url
  local f="$1"
  if [ ! -s "$f" ]; then
    curl -sSL --max-time 240 -o "$f" "$2" && echo "OK  $f $(stat -c%s "$f")" || echo "FAIL $f"
  else echo "HAVE $f"; fi
}
fetch com.forrestguice.suntimeswidget_135.apk "https://f-droid.org/repo/com.forrestguice.suntimeswidget_135.apk"
fetch SKIP_asteroids "https://invalid.example"
fetch de.georgsieber.ballbreak_10.apk "https://f-droid.org/repo/de.georgsieber.ballbreak_10.apk"
echo DONE
