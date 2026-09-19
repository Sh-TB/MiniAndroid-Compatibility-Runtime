#!/usr/bin/env bash
# S64 staging: 3 new candidates → build_fixture_apk.sh-compatible dirs.
# Documented law (anuto/gmdice/siggen precedent): AGP8 manifests lack
# package= → staged manifest gains package=<namespace>; BuildConfig.java
# generated per AGP contract when referenced by app code.
set -euo pipefail
OUT=/tmp/s64_stage
rm -rf "$OUT"; mkdir -p "$OUT/pmk" "$OUT/klondike" "$OUT/shopcalc"

# ---- NEW-001: pmk-android @ 100eea1 (repo ahead: v3.3.6/vc336) ----
S=/tmp/cand/pmk-android/pmk/app/src/main
cp -r "$S/java" "$OUT/pmk/src"
cp -r "$S/res" "$OUT/pmk/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/pmk/assets"
sed 's|<manifest xmlns:android="http://schemas.android.com/apk/res/android">|<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.cax.pmk" android:versionCode="336" android:versionName="3.3.6">|' "$S/AndroidManifest.xml" > "$OUT/pmk/AndroidManifest.xml"
mkdir -p "$OUT/pmk/src/com/cax/pmk"
cat > "$OUT/pmk/src/com/cax/pmk/BuildConfig.java" <<'EOF'
/** Generated per AGP contract (google flavor: no donation info). */
package com.cax.pmk;

public final class BuildConfig {
  public static final boolean DEBUG = false;
  public static final boolean IS_DONATION_INFO_ENABLED = false;
}
EOF

# ---- NEW-002: FreeKlondike @ 789dba5 (manifest already v2.0.1/vc3) ----
S=/tmp/cand/FreeKlondike/FreeKlondike/src/main
cp -r "$S/java" "$OUT/klondike/src"
cp -r "$S/res" "$OUT/klondike/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/klondike/assets"
python3 - "$S/AndroidManifest.xml" "$OUT/klondike/AndroidManifest.xml" <<'EOF'
import sys, re
src = open(sys.argv[1]).read()
src = src.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android"',
                  '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="eu.veldsoft.free.klondike"', 1)
open(sys.argv[2], "w").write(src)
EOF

# ---- NEW-003: shopping-list-calc @ e1d3f74 (v2.0/vc15) ----
S=/tmp/cand/shopping-list-calc/app/src/main
cp -r "$S/java" "$OUT/shopcalc/src"
cp -r "$S/res" "$OUT/shopcalc/res"
[ -d "$S/assets" ] && cp -r "$S/assets" "$OUT/shopcalc/assets"
python3 - "$S/AndroidManifest.xml" "$OUT/shopcalc/AndroidManifest.xml" <<'EOF'
import sys
src = open(sys.argv[1]).read()
src = src.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
                  '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="io.github.buildsbyben.shoppinglistcalc" android:versionCode="15" android:versionName="2.0">', 1)
open(sys.argv[2], "w").write(src)
EOF

echo "STAGED:"; for d in pmk klondike shopcalc; do echo "  $d: $(find $OUT/$d/src -name '*.java' | wc -l) java, res=$(du -sh $OUT/$d/res | cut -f1)"; done
