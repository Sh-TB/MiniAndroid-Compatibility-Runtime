#!/usr/bin/env bash
# scripts/build/bootstrap_toolchain.sh — AE gate: one-command toolchain recovery.
#
# WHY: the campaign lost fixture-build stages (rc=2) after a container
# reset because /home/z/my-project/tools/aapt2 was not reproducible from
# the repo. This script restores every external tool from its documented,
# hash-verifiable source. Idempotent: skips tools that already exist.
#
# Sources (documented in docs/research/GITHUB_RESEARCH_INDEX.md):
#   aapt2   8.13.2-14304508  Google Maven (Apache-2.0)
#   ecj     ECJ jar          MIT        (already vendored path-checked here)
#   d8/r8   r8.jar           Apache-2.0
#   stubs   android-34.jar   Apache-2.0 AOSP stubs
#
# Usage: bash scripts/build/bootstrap_toolchain.sh
set -euo pipefail
TOOLS="${TOOLS:-/home/z/my-project/tools}"
ROOT="${ROOT:-/home/z/my-project}"
mkdir -p "$TOOLS/aapt2" "$TOOLS/d8" "$TOOLS/ecj"

AAPT2="$TOOLS/aapt2/aapt2"
AAPT2_URL="https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.13.2-14304508/aapt2-8.13.2-14304508-linux.jar"

if [ -x "$AAPT2" ] && "$AAPT2" version >/dev/null 2>&1; then
    echo "aapt2: present ($("$AAPT2" version 2>&1 | head -1))"
else
    echo "aapt2: restoring from $AAPT2_URL"
    TMP="$(mktemp -d)"
    curl -sSL -o "$TMP/aapt2.jar" "$AAPT2_URL"
    unzip -o -q "$TMP/aapt2.jar" aapt2 -d "$TMP"
    mv "$TMP/aapt2" "$AAPT2"
    chmod +x "$AAPT2"
    rm -rf "$TMP"
    "$AAPT2" version
fi

# ECJ 3.33.0 — Eclipse Maven (public mirror of the vendored jar)
ECJ="$TOOLS/ecj/ecj.jar"
if [ -f "$ECJ" ]; then echo "ok: $ECJ"; else
    echo "ecj: restoring from Maven Central"
    curl -sfSL -o "$ECJ" "https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/3.33.0/ecj-3.33.0.jar"
fi

# r8 8.13.23 (d8 included) — Google Maven
R8="$TOOLS/d8/r8.jar"
if [ -f "$R8" ]; then echo "ok: $R8"; else
    echo "r8: restoring from Google Maven"
    curl -sfSL -o "$R8" "https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.13.23/r8-8.13.23.jar"
fi

# android-34 framework stubs — Google Maven artifact is not public; use the
# Robolectric android-all-14 (API 34) mirror on Maven Central (-f: fail on 404,
# never save an HTML error page as a jar).
A34="$TOOLS/android-34.jar"
if [ -f "$A34" ] && [ "$(head -c2 "$A34" | xxd -p)" = "504b" ]; then echo "ok: $A34"; else
    echo "android-34 stubs: restoring from Maven Central (robolectric android-all-14)"
    curl -sfSL -o "$A34" "https://repo1.maven.org/maven2/org/robolectric/android-all/14-robolectric-10818077-i7/android-all-14-robolectric-10818077-i7.jar" \
        || curl -sfSL -o "$A34" "https://repo1.maven.org/maven2/org/robolectric/android-all/14-robolectric-10818077/android-all-14-robolectric-10818077.jar"
fi

for f in "$TOOLS/ecj/ecj.jar" "$TOOLS/d8/r8.jar" "$TOOLS/android-34.jar"; do
    if [ -f "$f" ]; then echo "ok: $f"; else echo "MISSING: $f (vendored asset — restore from backup)" >&2; fi
done

# ── S101: virtual system-image fonts (G32 monospace law) ──────────────────
# text_shaper resolves family 'monospace' -> runtime/data/fonts/DroidSansMono.ttf
# (AOSP fonts.xml law). The dir is gitignored by design (binary system image),
# so a container reset loses it — the READY banner then reports monospace=MISSING
# on EVERY run. Fetch + SHA-verify idempotently here.
FONT_DIR="$ROOT/runtime/data/fonts"
FONT_FILE="$FONT_DIR/DroidSansMono.ttf"
FONT_SHA="db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862"
if [ -f "$FONT_FILE" ] && [ "$(sha256sum "$FONT_FILE" | cut -d' ' -f1)" = "$FONT_SHA" ]; then
    echo "ok: $FONT_FILE"
else
    echo "fonts: restoring DroidSansMono.ttf (AOSP platform/frameworks/base data/fonts)"
    mkdir -p "$FONT_DIR"
    curl -sfSL "https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/data/fonts/DroidSansMono.ttf?format=TEXT" | base64 -d > "$FONT_FILE"
    if [ "$(sha256sum "$FONT_FILE" | cut -d' ' -f1)" = "$FONT_SHA" ]; then
        echo "ok: $FONT_FILE (sha verified)"
    else
        echo "MISSING: DroidSansMono.ttf sha mismatch — monospace family will report MISSING" >&2
    fi
fi

echo "TOOLCHAIN BOOTSTRAP COMPLETE"
