#!/usr/bin/env bash
# ============================================================================
# package_release.sh — build a clean, validated MiniAndroid release package.
#
# Guarantees enforced here (born from the build-win toolchain-leak incident):
#   1. staging is created FRESH every run — never reused, never incremental
#   2. ONLY the intended runtime files are copied into staging (no tree copies)
#   3. scripts/validate_release_content.py gates BOTH the staging trees and
#      the final archives; any toolchain/development content aborts the build
#   4. a SHA256 manifest is emitted next to the archives
#
# Usage:
#   scripts/package_release.sh --version v0.0.2-Australorp \
#       [--linux-bin miniandroid/build/miniandroid] \
#       [--win-exe  miniandroid/build-win/MiniAndroid.exe] \
#       [--demo-apk demo/build/miniandroid-demo.apk] \
#       [--out release_staging]
#
# Outputs (under --out):
#   MiniAndroid-<version>-linux-x64.tar.gz
#   MiniAndroid-<version>-windows-x64.zip
#   SHA256SUMS.txt
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VERSION=""
LINUX_BIN="miniandroid/build/miniandroid"
WIN_EXE="miniandroid/build-win/MiniAndroid.exe"
DEMO_APK="demo/build/miniandroid-demo.apk"
OUT="release_staging"

while [ $# -gt 0 ]; do
  case "$1" in
    --version)  VERSION="$2"; shift 2 ;;
    --linux-bin) LINUX_BIN="$2"; shift 2 ;;
    --win-exe)  WIN_EXE="$2"; shift 2 ;;
    --demo-apk) DEMO_APK="$2"; shift 2 ;;
    --out)      OUT="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

[ -n "$VERSION" ] || { echo "ERROR: --version is required" >&2; exit 2; }

echo "[package] version : $VERSION"
echo "[package] staging : fresh directory under $OUT (any previous one is removed)"

# ---- 0. verify inputs BEFORE touching staging ------------------------------
check_elf() { head -c4 "$1" | grep -q $'\x7fELF'; }
check_pe()  { head -c2 "$1" | grep -q 'MZ'; }

[ -f "$LINUX_BIN" ] && check_elf "$LINUX_BIN" \
  || { echo "ERROR: Linux binary missing or not ELF: $LINUX_BIN" >&2; exit 1; }
[ -f "$WIN_EXE" ] && check_pe "$WIN_EXE" \
  || { echo "ERROR: Windows exe missing or not PE: $WIN_EXE" >&2; exit 1; }
[ -f "$DEMO_APK" ] \
  || { echo "ERROR: demo APK missing: $DEMO_APK (run demo/build_demo_apk.sh)" >&2; exit 1; }
[ -f "scripts/release/run-miniandroid.sh" ] \
  || { echo "ERROR: template missing: scripts/release/run-miniandroid.sh" >&2; exit 1; }

# ---- 1. fresh staging ------------------------------------------------------
STAGE="$OUT/pkg-$VERSION"
rm -rf "$STAGE"
mkdir -p "$STAGE"

LINUX_DIR="$STAGE/MiniAndroid-$VERSION-linux-x64"
WIN_DIR="$STAGE/MiniAndroid-$VERSION-windows-x64"
mkdir -p "$LINUX_DIR" "$WIN_DIR"

# ---- 2. copy ONLY the intended runtime files -------------------------------
echo "[package] copying runtime files (explicit list, no tree copies)"

# Linux: strip the binary into staging (development symbols stay in the build tree)
cp "$LINUX_BIN" "$LINUX_DIR/miniandroid"
if command -v strip >/dev/null 2>&1; then
  strip "$LINUX_DIR/miniandroid"
  echo "[package] linux binary stripped: $(du -h "$LINUX_DIR/miniandroid" | cut -f1)"
fi
chmod +x "$LINUX_DIR/miniandroid"
install -m 755 scripts/release/run-miniandroid.sh "$LINUX_DIR/run-miniandroid.sh"
sed "s/__VERSION__/$VERSION/" scripts/release/README-linux.txt > "$LINUX_DIR/README.txt"
cp LICENSE "$LINUX_DIR/LICENSE"
cp "$DEMO_APK" "$LINUX_DIR/miniandroid-demo.apk"

# Windows: no DLLs are bundled by design (the exe imports only UCRT + KERNEL32)
cp "$WIN_EXE" "$WIN_DIR/MiniAndroid.exe"
sed "s/__VERSION__/$VERSION/" scripts/release/README-windows.txt > "$WIN_DIR/README.txt"
cp LICENSE "$WIN_DIR/LICENSE"
cp "$DEMO_APK" "$WIN_DIR/miniandroid-demo.apk"

# ---- 3. validate the staging trees ------------------------------------------
echo "[package] validating staging trees (release-content gate)"
python3 scripts/validate_release_content.py --platform linux   "$LINUX_DIR"
python3 scripts/validate_release_content.py --platform windows "$WIN_DIR"

# ---- 4. create archives ------------------------------------------------------
echo "[package] creating archives"
TARGZ="$OUT/MiniAndroid-$VERSION-linux-x64.tar.gz"
ZIP="$OUT/MiniAndroid-$VERSION-windows-x64.zip"
rm -f "$TARGZ" "$ZIP"
tar czf "$TARGZ" -C "$STAGE" "MiniAndroid-$VERSION-linux-x64"
if command -v zip >/dev/null 2>&1; then
  ( cd "$STAGE" && zip -q -r "$OLDPWD/$ZIP" "MiniAndroid-$VERSION-windows-x64" )
else
  python3 - "$STAGE" "$ZIP" << 'PYEOF'
import os, sys, zipfile
stage, zout = sys.argv[1], sys.argv[2]
root = "MiniAndroid-" + os.path.basename(stage).replace("pkg-", "")
with zipfile.ZipFile(zout, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _dirs, files in os.walk(os.path.join(stage, root)):
        for f in files:
            full = os.path.join(base, f)
            z.write(full, os.path.relpath(full, stage))
PYEOF
fi

# ---- 5. validate the ARCHIVES themselves ------------------------------------
echo "[package] validating final archives (release-content gate)"
python3 scripts/validate_release_content.py --platform linux   "$TARGZ"
python3 scripts/validate_release_content.py --platform windows "$ZIP"

# ---- 6. SHA256 manifest ------------------------------------------------------
SUMS="$OUT/SHA256SUMS.txt"
{
  sha256sum "$TARGZ" "$ZIP" | sed "s|$OUT/||"
} > "$SUMS"

echo
echo "[package] ================================================================"
echo "[package] RELEASE PACKAGING: PASS"
echo "[package]   $TARGZ  ($(du -h "$TARGZ" | cut -f1))"
echo "[package]   $ZIP  ($(du -h "$ZIP" | cut -f1))"
echo "[package]   $SUMS"
echo "[package] staging tree kept for inspection: $STAGE"
echo "[package] ================================================================"
