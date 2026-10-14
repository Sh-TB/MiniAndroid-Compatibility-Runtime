#!/bin/bash
# cont12_build_oracle.sh — CONT-12 PHASE 2: build the BOUND EXTERNAL COMPOSE
# ORACLE probe APK (B2): a real Kotlin/@Composable app compiled against the
# EXACT real Maven Compose artifacts matching the dooz APK (see
# evidence/cont12/DOOZ_COMPOSE_DEPENDENCY_MATRIX.md), NO R8 (real names),
# mirroring dooz's chain: setContent -> MaterialTheme -> NavHost ->
# destination -> Text -> measure/layout -> draw.
#
# This is a TEST-ONLY oracle artifact. It does NOT touch MiniAndroid
# architecture and is NOT a permanent integration.
set -euo pipefail
BASE=/home/z/my-project
KOTLINC=$BASE/upstream/cont12_maven/kotlinc-dist/kotlinc
FIX=$BASE/fixtures/cont12_oracle
WORK=$BASE/tmp/cont12_oracle_build
OUT=$BASE/run/w8
CLS=$BASE/upstream/cont12_maven/classes
AAPT2=$BASE/tools/toolchain/aapt2
BOOT=$BASE/tools/toolchain/android-34.jar
D8JAR=$BASE/tools/toolchain/r8.jar

mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" "$FIX/src/com/probe/oracle12" "$OUT"

# ── 1) Kotlin probe source (mirrors dooz's structure) ────────────────────
cat > "$FIX/src/com/probe/oracle12/MainActivity.kt" << 'EOF'
package com.probe.oracle12

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val nav = rememberNavController()
                    var phase by remember { mutableStateOf("ready") }
                    LaunchedEffect(Unit) {
                        phase = "playing"
                    }
                    NavHost(navController = nav, startDestination = "game") {
                        composable("game") {
                            Column {
                                Text(text = "dooz-oracle phase=$phase")
                                Text(text = "connect-four board")
                            }
                        }
                    }
                }
            }
        }
    }
}
EOF

cat > "$FIX/AndroidManifest.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.probe.oracle12" android:versionCode="1" android:versionName="1.0">
    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34"/>
    <application android:label="Oracle12">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
EOF

# ── 2) resources: faithful merged-arsc from cont12_oracle_res2.sh (fallback:
#    manifest-only link when the res build has not run) ────────────────────
RESAPK=$BASE/tmp/cont12_resbuild/apk/resources.apk
if [ -f "$RESAPK" ]; then
  cp "$RESAPK" "$WORK/apk/resources.apk"
  echo "using merged library resources: $(stat -c%s "$RESAPK") bytes"
else
  "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
    --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
fi

# ── 3) kotlinc with the REAL compose compiler plugin, against REAL jars ──
CP="$BOOT:$CLS/kotlin-stdlib.jar"
for j in runtime-android runtime-saveable-android runtime-retain-android ui-android \
         ui-geometry-android ui-graphics-android ui-text-android ui-unit-android \
         ui-util-android foundation-android foundation-layout-android animation-android \
         animation-core-android material-ripple-android material-icons-core-android \
         material3-android material3-window-size-class-android activity activity-compose \
         activity-ktx lifecycle-runtime-android lifecycle-runtime-ktx-android \
         lifecycle-runtime-compose-android lifecycle-viewmodel-android \
         lifecycle-viewmodel-compose-android lifecycle-viewmodel-savedstate-android \
         lifecycle-livedata lifecycle-livedata-core lifecycle-common lifecycle-process \
         navigation-compose-android navigation-runtime-android navigation-common-android \
         navigationevent-android navigationevent-compose-android core core-ktx \
         core-viewtree savedstate-android savedstate-compose-android annotation-experimental \
         customview-poolingcontainer emoji2 startup-runtime tracing profileinstaller autofill \
         core-runtime core-common kotlinx-coroutines-core-jvm kotlinx-coroutines-android \
         atomicfu-jvm kotlinx-collections-immutable-jvm; do
  CP="$CP:$CLS/$j.jar"
done

java -Xmx2g -cp "$KOTLINC/lib/kotlin-compiler.jar" org.jetbrains.kotlin.cli.jvm.K2JVMCompiler \
  -no-stdlib -no-jdk -jvm-target 1.8 \
  -cp "$CP" \
  -Xplugin="$KOTLINC/lib/compose-compiler-plugin.jar" \
  -d "$WORK/obj" \
  "$FIX/src/com/probe/oracle12/MainActivity.kt"

# ── 4) D8: probe classes + ALL real dependency classes -> dex ────────────
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
if [ -f "$BASE/tmp/cont12_resbuild/rclasses.jar" ]; then
  echo "$BASE/tmp/cont12_resbuild/rclasses.jar" >> "$WORK/classes.txt"
fi
for j in "$CLS"/*.jar; do
  if [ -f "$j" ] && head -c 2 "$j" | grep -q "PK"; then echo "$j" >> "$WORK/classes.txt"; fi
done
java -Xmx2g -cp "$D8JAR" com.android.tools.r8.D8 --release --min-api 26 \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"

# ── 5) assemble the test APK ─────────────────────────────────────────────
cp "$WORK/apk/resources.apk" "$OUT/oracle12.apk"
cd "$WORK/dex" && for d in *.dex; do zip -j -X "$OUT/oracle12.apk" "$d" > /dev/null; done
cd "$BASE"
echo "oracle12.apk: $(sha256sum "$OUT/oracle12.apk" | cut -c1-16) ($(stat -c%s "$OUT/oracle12.apk") bytes)"
unzip -l "$OUT/oracle12.apk" | grep -c "classes.*dex" || true
