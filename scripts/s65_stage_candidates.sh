#!/usr/bin/env bash
# S65 staging: 3 new candidates -> build_fixture_apk.sh-compatible dirs.
# Law (anuto/gmdice/siggen/pmk/klondike/shopcalc precedent): copy src/main
# {java,res,assets} into the fixture layout; stage package=/versionCode/Name
# into AGP8-style manifests when missing; generate BuildConfig.java only
# when the app code references it.
set -euo pipefail
OUT=/tmp/s65_stage
rm -rf "$OUT"; mkdir -p "$OUT/tripeaks" "$OUT/fishrings" "$OUT/opmt"

# ---- NEW-001: TriPeaks @ 62f3609 (manifest already package= vc4 v1.2.1) ----
S=/tmp/cand/TriPeaksSolitaireForAndroid/TriPeaksSolitaireForAndroid/src/main
cp -r "$S/java" "$OUT/tripeaks/src"
cp -r "$S/res" "$OUT/tripeaks/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/tripeaks/assets"
cp "$S/AndroidManifest.xml" "$OUT/tripeaks/AndroidManifest.xml"

# ---- NEW-002: FishRings @ dc3807e (manifest has package=; stage vc/name) ----
S=/tmp/cand/FishRingsForAndroid/FishRingsForAndroid/src/main
cp -r "$S/java" "$OUT/fishrings/src"
cp -r "$S/res" "$OUT/fishrings/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/fishrings/assets"
python3 - "$S/AndroidManifest.xml" "$OUT/fishrings/AndroidManifest.xml" <<'EOF'
import sys
src = open(sys.argv[1]).read()
src = src.replace('package="eu.veldsoft.fish.rings">',
                  'package="eu.veldsoft.fish.rings" android:versionCode="6" android:versionName="1.23">', 1)
open(sys.argv[2], "w").write(src)
EOF

# ---- NEW-003: OPMT @ 3240c4cf (manifest has package=; stage vc/name) ----
S=/tmp/cand/OPMT/app/src/main
cp -r "$S/java" "$OUT/opmt/src"
cp -r "$S/res" "$OUT/opmt/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/opmt/assets"
python3 - "$S/AndroidManifest.xml" "$OUT/opmt/AndroidManifest.xml" <<'EOF'
import sys, re
src = open(sys.argv[1]).read()
if 'android:versionCode' not in src:
    src = src.replace('package="one.scarecrow.games.OPMT">',
                      'package="one.scarecrow.games.OPMT" android:versionCode="1" android:versionName="0.1.2">', 1)
open(sys.argv[2], "w").write(src)
EOF
# OPMT staged-styles transform (siggen law): the app theme references
# AppCompat/Material Components library attrs absent from the standalone
# aapt2 stub table. Re-parent to framework Material themes, drop library
# attr items, resolve statusBarColor to a literal color. Build-level
# adaptation only; recorded in the S65 report.
python3 - "$OUT/opmt" <<'EOF'
import re, sys
base = sys.argv[1]
for f, parent in ((f"{base}/res/values/themes.xml", "android:Theme.Material.Light.NoActionBar"),
                  (f"{base}/res/values-night/themes.xml", "android:Theme.Material.NoActionBar")):
    try:
        s = open(f).read()
    except FileNotFoundError:
        continue
    s = re.sub(r'parent="Theme\.(AppCompat|MaterialComponents|Design)[^"]*"', f'parent="{parent}"', s)
    for attr in ("colorPrimary", "colorOnPrimary", "colorSecondary",
                 "colorPrimaryVariant", "colorSecondaryVariant", "colorOnSecondary"):
        s = re.sub(r'\s*<item name="%s">[^<]*</item>' % attr, "", s)
    s = s.replace("?attr/colorPrimaryVariant", "@color/purple_700")
    s = s.replace(' xmlns:tools="http://schemas.android.com/tools"', "")
    s = re.sub(r' tools:targetApi="l"', "", s)
    open(f, "w").write(s)
print("opmt themes transformed")
EOF
# OPMT staged-layouts transform: ConstraintLayout (library-provided) is not
# in the standalone resource table. activity_main_menu 4 buttons -> FrameLayout
# with gravity/anchor margins; activity_settings empty root -> FrameLayout.
# Game board layout (activity_game.xml) is constraint-free and untouched;
# ids preserved so MainMenu/settingsActivity code binds unchanged.
python3 - "$OUT/opmt" <<'EOF'
import sys, re
base = sys.argv[1]
p = f"{base}/res/layout/activity_main_menu.xml"
open(p, "w").write('''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/homescreenwithtext">

    <Button
        android:id="@+id/settingsBtn"
        android:layout_width="36dp"
        android:layout_height="36dp"
        android:layout_gravity="top|end"
        android:layout_marginTop="14dp"
        android:layout_marginEnd="18dp"
        android:background="@drawable/gear" />

    <LinearLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_gravity="bottom|center_horizontal"
        android:layout_marginBottom="28dp"
        android:orientation="vertical">

        <Button
            android:id="@+id/playbtn2"
            android:layout_width="200dp"
            android:layout_height="50dp"
            android:layout_marginBottom="14dp"
            android:background="@drawable/mainmenubutton"
            android:text="@string/play_with_friend" />

        <Button
            android:id="@+id/playbtn"
            android:layout_width="200dp"
            android:layout_height="50dp"
            android:layout_marginBottom="14dp"
            android:background="@drawable/mainmenubutton"
            android:text="@string/play_with_computer" />

        <Button
            android:id="@+id/howPlayBtn"
            android:layout_width="200dp"
            android:layout_height="50dp"
            android:background="@drawable/mainmenubutton"
            android:text="@string/how_to_play" />
    </LinearLayout>
</FrameLayout>
''')
p2 = f"{base}/res/layout/activity_settings.xml"
open(p2, "w").write('''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
</FrameLayout>
''')
print("opmt layouts transformed")
EOF
# androidx compile-stub (android-34-stubs law applied to appcompat): OPMT
# compiles against 2 androidx symbols. Compile-time stub only — runtime
# behavior is the app's own DEX on the engine's Activity lifecycle:
#   AppCompatActivity = Activity passthrough (real androidx onCreate
#   delegation is replaced by the engine's generic inflation, proven by
#   the dooz/anuto runtime paths).
#   AppCompatDelegate.setDefaultNightMode = no-op + MODE_NIGHT_YES const
#   (inlined at compile; the night-visual toggle is stubbed honestly).
mkdir -p "$OUT/opmt/src/androidx/appcompat/app"
cat > "$OUT/opmt/src/androidx/appcompat/app/AppCompatActivity.java" <<'EOF'
package androidx.appcompat.app;

import android.app.Activity;

/** COMPILE-TIME STUB (android-34-stubs law). Engine maps Activity lifecycle. */
public class AppCompatActivity extends Activity {
}
EOF
cat > "$OUT/opmt/src/androidx/appcompat/app/AppCompatDelegate.java" <<'EOF'
package androidx.appcompat.app;

/** COMPILE-TIME STUB (android-34-stubs law). Night-mode toggle is a no-op. */
public final class AppCompatDelegate {
    public static final int MODE_NIGHT_NO = 1;
    public static final int MODE_NIGHT_YES = 2;
    public static final int MODE_NIGHT_FOLLOW_SYSTEM = -1;

    private AppCompatDelegate() {
    }

    public static void setDefaultNightMode(int mode) {
        // no-op in the compile-stub build
    }
}
EOF
echo "androidx compile-stubs generated"
# app:srcCompat (AppCompat attr) -> android:src (framework attr) — the
# standard standalone-compile bridge; ImageView drawables render identically.
python3 - "$OUT/opmt" <<'EOF'
import sys, re, glob
base = sys.argv[1]
for f in glob.glob(f"{base}/res/layout/*.xml"):
    s = open(f).read()
    n = re.sub(r'app:srcCompat="', 'android:src="', s)
    n = n.replace(' xmlns:app="http://schemas.android.com/apk/res-auto"', "")
    if n != s:
        open(f, "w").write(n)
        print("  srcCompat bridged:", f)
EOF

echo "STAGED:"
for d in tripeaks fishrings opmt; do
  echo "  $d: src=$(find $OUT/$d/src -name '*.java' | wc -l) java, res_entries=$(find $OUT/$d/res -type f | wc -l), manifest_vc=$(grep -o 'versionCode="[^"]*"' $OUT/$d/AndroidManifest.xml | head -1)"
done