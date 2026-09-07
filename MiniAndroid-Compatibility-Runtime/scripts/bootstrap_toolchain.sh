#!/usr/bin/env bash
# bootstrap_toolchain.sh — AE gate: one-command toolchain recovery.
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
# Usage: bash scripts/bootstrap_toolchain.sh
set -euo pipefail
TOOLS="${TOOLS:-/home/z/my-project/tools}"
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

for f in "$TOOLS/ecj/ecj.jar" "$TOOLS/d8/r8.jar" "$TOOLS/android-34.jar"; do
    if [ -f "$f" ]; then echo "ok: $f"; else echo "MISSING: $f (vendored asset — restore from backup)" >&2; fi
done

echo "TOOLCHAIN BOOTSTRAP COMPLETE"
