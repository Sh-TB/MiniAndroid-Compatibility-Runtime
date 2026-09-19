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
# Material Components library attrs (colorPrimaryVariant/colorSecondaryVariant/
# colorOnSecondary) absent from the standalone aapt2 stub table. Drop those
# items, resolve statusBarColor to a literal color. Build-level adaptation
# only; recorded in the S65 report.
python3 - "$OUT/opmt" <<'EOF'
import re, sys
base = sys.argv[1]
for f in (f"{base}/res/values/themes.xml", f"{base}/res/values-night/themes.xml"):
    try:
        s = open(f).read()
    except FileNotFoundError:
        continue
    for attr in ("colorPrimaryVariant", "colorSecondaryVariant", "colorOnSecondary"):
        s = re.sub(r'\s*<item name="%s">[^<]*</item>' % attr, "", s)
    s = s.replace("?attr/colorPrimaryVariant", "@color/purple_700")
    s = s.replace(' xmlns:tools="http://schemas.android.com/tools"', "")
    s = re.sub(r' tools:targetApi="l"', "", s)
    open(f, "w").write(s)
print("opmt themes transformed")
EOF

echo "STAGED:"
for d in tripeaks fishrings opmt; do
  echo "  $d: src=$(find $OUT/$d/src -name '*.java' | wc -l) java, res_entries=$(find $OUT/$d/res -type f | wc -l), manifest_vc=$(grep -o 'versionCode="[^"]*"' $OUT/$d/AndroidManifest.xml | head -1)"
done