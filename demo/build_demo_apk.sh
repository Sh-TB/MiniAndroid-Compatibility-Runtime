#!/usr/bin/env bash
# build_demo_apk.sh — build the MiniAndroid execution-proof demo APK.
#
# CYCLE-E: this now DELEGATES to scripts/build_fixture_apk.sh — the single,
# inner-class-safe, fail-loud APK builder (ECJ → D8 → package). The previous
# inline copy had exactly the three defects the fixture tool was written to
# kill: `|| true` on ECJ (silent compile failures), `$(find ...)` piping
# class files through word splitting, and a `python3 -` heredoc using
# `Path(__file__)` which does not exist for stdin scripts (packaging read
# AndroidManifest.xml from the CWD instead of the demo dir — demo packaging
# was broken at HEAD ad95d928 whenever CWD ≠ demo/).
#
# The manifest is PLAIN TEXT XML: MiniAndroid's manifest_reader parses both
# binary AXML and plain XML, and this app uses no compiled resources.
#
# Toolchain (via the shared fixture tool, all official open-source releases,
# no Android SDK required): ECJ (MIT) → D8/r8 (Apache-2.0) → python zipfile.
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEMO_DIR/.." && pwd)"
OUT_DIR="$DEMO_DIR/build"

mkdir -p "$OUT_DIR"
bash "$REPO_ROOT/scripts/build_fixture_apk.sh" "$DEMO_DIR" "$OUT_DIR/miniandroid-demo.apk"
echo "demo APK ready: $OUT_DIR/miniandroid-demo.apk"
