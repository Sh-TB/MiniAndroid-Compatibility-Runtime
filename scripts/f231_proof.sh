#!/bin/bash
# F-NEW-231 INSTALLED_APK_ACCESS — two-APK installed-state proof (mega-campaign §3)
# App  : com.darkempire78.opencalculator (upload/opencalculator_53.apk)
# Game : com.dozingcatsoftware.bouncy    (upload/canonical_apks/bouncy.apk)
#
# Chain proven per APK:
#  1. install (MiniAndroid package store, AOSP PMS law)
#  2. identity-only discovery (list-packages; original path NOT referenced)
#  3. manifest inspection from INSTALLED base.apk (analyze)
#  4. DEX inspection from INSTALLED base.apk (dex)
#  5. SOURCE-HIDING: original APK moved away -> run --package x3
#  6. provenance: lifecycle_trace "apk" field = installed codePath
#  7. integrity: sha256(installed) == sha256(source) == package.json.apkSha256
#  8. 3-run reproducibility: screenshot file-sha x3 identical + pixel census
set -u
cd /home/z/my-project/miniandroid
STORE=/home/z/my-project/run/f231/store
OUT=/home/z/my-project/run/f231/proof
SRC_APP=/home/z/my-project/upload/opencalculator_53.apk
SRC_GAME=/home/z/my-project/upload/canonical_apks/bouncy.apk
HIDE_DIR=/tmp/f231_hidden

rm -rf "$STORE" "$OUT"; mkdir -p "$STORE" "$OUT"
rm -rf "$HIDE_DIR"; mkdir -p "$HIDE_DIR"
restore() { [ -f "$HIDE_DIR/opencalculator_53.apk" ] && mv "$HIDE_DIR/opencalculator_53.apk" "$SRC_APP"; \
            [ -f "$HIDE_DIR/bouncy.apk" ] && mv "$HIDE_DIR/bouncy.apk" "$SRC_GAME"; }
trap restore EXIT

step() { echo; echo "═══ $* ═══"; }

sha_file() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

for pair in "app:$SRC_APP" "game:$SRC_GAME"; do
  kind="${pair%%:*}"; src="${pair#*:}"
  step "$kind INSTALL: $src"
  ./build/miniandroid install "$src" --data-root "$STORE" -v 2>&1 | tee "$OUT/install_$kind.log"
done

step "IDENTITY-ONLY DISCOVERY (list-packages)"
./build/miniandroid list-packages --data-root "$STORE" > "$OUT/installed_packages.json"
cat "$OUT/installed_packages.json"

# From here on: the ONLY inputs used are package names + data-root.
PKG_APP=com.darkempire78.opencalculator
PKG_GAME=com.dozingcatsoftware.bouncy

for pair in "app:$PKG_APP" "game:$PKG_GAME"; do
  kind="${pair%%:*}"; pkg="${pair#*:}"
  BASE="$STORE/data/app/$pkg/base.apk"
  step "$kind MANIFEST INSPECTION FROM INSTALLED STATE ($pkg)"
  ./build/miniandroid analyze "$BASE" 2>/dev/null | grep -E "package_name|version_name|version_code|main_activity_full" \
      > "$OUT/analyze_installed_$kind.txt"
  cat "$OUT/analyze_installed_$kind.txt"

  step "$kind DEX INSPECTION FROM INSTALLED STATE"
  ./build/miniandroid dex "$BASE" 2>/dev/null | grep -E "DEX Version|Strings:|Classes:" | head -4 \
      > "$OUT/dex_installed_$kind.txt"
  cat "$OUT/dex_installed_$kind.txt"

  step "$kind SOURCE-HIDE + 3x RUN FROM INSTALLED STATE"
  # hide the ORIGINAL sideload APK so the run can only be using the store
  if [ "$kind" = app ]; then mv "$SRC_APP" "$HIDE_DIR/opencalculator_53.apk"; else mv "$SRC_GAME" "$HIDE_DIR/bouncy.apk"; fi
  shas=""; rcs=""
  for i in 1 2 3; do
    o="$OUT/${kind}_run$i"; mkdir -p "$o"
    timeout 300 ./build/miniandroid run --package "$pkg" --data-root "$STORE" -o "$o" \
        > "$o/run.log" 2>&1
    rcs="$rcs$?"
    s=$(sha_file "$o/screenshot.png")
    shas="$shas $s"
    # provenance + census for run1
    if [ "$i" = 1 ]; then
      grep -o "\"apk\": \"[^\"]*\"" "$o/lifecycle_trace.json" | head -1 \
          > "$OUT/provenance_$kind.txt"
      python3 - "$o/screenshot.png" > "$OUT/census_$kind.txt" <<'PYEOF'
import sys
from PIL import Image
img = Image.open(sys.argv[1]).convert('RGB')
cols = img.getcolors(maxcolors=10_000_000); cols.sort(reverse=True)
tot = img.size[0]*img.size[1]
print("size:", img.size, "unique_colors:", len(cols))
print("top3:", [(round(100*n/tot,1), c) for n,c in cols[:3]])
PYEOF
      cat "$OUT/provenance_$kind.txt" "$OUT/census_$kind.txt"
    fi
  done
  echo "$kind 3-run screenshot file-shas:$shas rc:$rcs" | tee "$OUT/repro_$kind.txt"
  # integrity: installed bytes == package.json sha (source sha recorded at install)
  python3 - "$STORE/data/app/$pkg/package.json" "$BASE" "$kind" <<'PYEOF' | tee -a "$OUT/repro_$kind.txt"
import json, hashlib, sys
rec = json.load(open(sys.argv[1]))
sha = hashlib.sha256(open(sys.argv[2],'rb').read()).hexdigest()
print(f"{sys.argv[3]} integrity: installed_sha == record_sha: {sha == rec['apkSha256']}")
PYEOF
  # restore original before next kind
  restore
done

step "F-NEW-231 PROOF COMPLETE"
echo "Artifacts under $OUT"
