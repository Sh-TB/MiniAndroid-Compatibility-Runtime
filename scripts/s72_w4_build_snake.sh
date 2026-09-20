#!/usr/bin/env bash
# s72_w4_build_snake.sh — source-first build of AndroidGameSnake
# (zhangman523/AndroidGameSnake @ b4968c39, Apache-2.0) with the canonical
# aapt2/ECJ/D8 toolchain (OPMT S65 recipe). App sources UNTOUCHED; only
# compile-stubs for com.android.support v7 are ADDED (packaged, same law).
set -euo pipefail
ROOT=/home/z/my-project
SRC=/tmp/snake_recon/AndroidGameSnake
B=$ROOT/upload/s72_w4_apks/.build_snake
TOOLS=$ROOT/tools

rm -rf "$B"; mkdir -p "$B"/{classes,rjava,dex,stub_src/android/support/v7/app,stub_src/android/support/annotation}
cd "$B"

# 1. compile-stubs (packaged; app code binds unchanged — OPMT S65 law)
cat > stub_src/android/support/v7/app/AppCompatActivity.java <<'EOF'
package android.support.v7.app;
import android.app.Activity;
import android.os.Bundle;
/** Compile-stub: compile-time type only; runtime semantics = android.app.Activity. */
public class AppCompatActivity extends Activity {
  public AppCompatActivity() {}
  @Override
  protected void onCreate(Bundle savedInstanceState) { super.onCreate(savedInstanceState); }
}
EOF
cat > stub_src/android/support/annotation/Nullable.java <<'EOF'
package android.support.annotation;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.CLASS)
public @interface Nullable {}
EOF

# 2. resources -> base.apk (with framework ids) + R.java
#    STAGED RES (siggen law, OPMT S65 precedent): the appcompat library is
#    not in the toolchain, so AppTheme's PARENT is re-staged to the platform
#    Material.Light theme and the three appcompat color attrs are declared
#    as app-local attrs. AppTheme name/id and every app reference unchanged;
#    staged files live OUTSIDE the app source tree.
mkdir -p staged_res/values
cat > staged_res/values/staged_theme.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
  <attr name="colorPrimary" format="color" />
  <attr name="colorPrimaryDark" format="color" />
  <attr name="colorAccent" format="color" />
  <style name="AppTheme" parent="@android:style/Theme.Material.Light">
    <item name="colorPrimary">@color/colorPrimary</item>
    <item name="colorPrimaryDark">@color/colorPrimaryDark</item>
    <item name="colorAccent">@color/colorAccent</item>
  </style>
</resources>
EOF
# ConstraintLayout attr IDs for aapt2 link (real library not in toolchain).
# Engine resolves AXML attrs BY NAME, so app-local IDs are semantics-neutral;
# the ENGINE implements the constraint semantics generically (F-NEW law).
python3 - <<'PYEOF'
attrs = """layout_constraintLeft_toLeftOf layout_constraintLeft_toRightOf
layout_constraintRight_toLeftOf layout_constraintRight_toRightOf
layout_constraintStart_toStartOf layout_constraintStart_toEndOf
layout_constraintEnd_toStartOf layout_constraintEnd_toEndOf
layout_constraintTop_toTopOf layout_constraintTop_toBottomOf
layout_constraintBottom_toTopOf layout_constraintBottom_toBottomOf
layout_constraintBaseline_toBaselineOf layout_constraintHorizontal_bias
layout_constraintVertical_bias layout_constraintWidth_default
layout_constraintHeight_default layout_constraintWidth_percent
layout_constraintHeight_percent layout_constraintDimensionRatio
layout_constraintHorizontal_weight layout_constraintVertical_weight
layout_constraintCircle layout_constraintCircleAngle layout_constraintCircleRadius
layout_constraintGuide_begin layout_constraintGuide_end layout_constraintGuide_percent
layout_constraintTag layout_constraintCreator""".split()
with open("staged_res/values/staged_constraint_attrs.xml", "w") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n')
    for a in attrs:
        f.write(f'  <attr name="{a}" format="string|reference" />\n')
    f.write('</resources>\n')
print("staged constraint attrs:", len(attrs))
PYEOF
rm "$SRC/app/src/main/res/values/styles.xml.disabled" 2>/dev/null || true
mv "$SRC/app/src/main/res/values/styles.xml" /tmp/snake_styles_orig.xml
"$TOOLS/aapt2/aapt2" compile --dir "$SRC/app/src/main/res" -o res_base.zip
"$TOOLS/aapt2/aapt2" compile --dir staged_res -o res_stage.zip
mv /tmp/snake_styles_orig.xml "$SRC/app/src/main/res/values/styles.xml"
"$TOOLS/aapt2/aapt2" link -o base.apk -I "$TOOLS/android-34.jar" \
  --manifest "$SRC/app/src/main/AndroidManifest.xml" \
  --java rjava --min-sdk-version 19 --target-sdk-version 26 \
  --version-code 1 --version-name 1.0 res_base.zip res_stage.zip --auto-add-overlay

# 3. compile (app sources untouched + generated R + stubs)
find "$SRC/app/src/main/java" "$B/rjava" "$B/stub_src" -name "*.java" > sources.txt
wc -l sources.txt
java -jar "$TOOLS/ecj/ecj.jar" -source 1.8 -target 1.8 -encoding UTF-8 \
  -cp "$TOOLS/android-34.jar" -d classes @sources.txt -nowarn -g

# 4. dex (canonical build_fixture_apk recipe: class tree -> deterministic
#    .jar first — inner-class-safe; D8 main class via -cp)
python3 - classes classes.jar <<'PY'
import sys, zipfile
from pathlib import Path
classes_dir, jar_path = Path(sys.argv[1]), Path(sys.argv[2])
files = sorted(p for p in classes_dir.rglob("*.class") if p.is_file())
with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.writestr(p.relative_to(classes_dir).as_posix(), p.read_bytes())
print(f"      jar entries: {len(files)}")
PY
java -cp "$TOOLS/d8/r8.jar" com.android.tools.r8.D8 \
  --release --lib "$TOOLS/android-34.jar" --output dex classes.jar
ls -la dex/

# 5. package
cp base.apk snake_v1.0_vc1.apk
(cd dex && zip -q ../snake_v1.0_vc1.apk classes.dex)
sha256sum snake_v1.0_vc1.apk
unzip -l snake_v1.0_vc1.apk | tail -5
echo "BUILD COMPLETE: $B/snake_v1.0_vc1.apk"
