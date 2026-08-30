#!/usr/bin/env bash
# Download + SHA256-verify test APKs into an EXTERNAL cache (CAMPAIGN 011 §20/§21).
# The repository itself must stay ZERO-APK. Cache default: ../apk_cache (outside repo).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="${MINIANDROID_APK_CACHE:-$(dirname "$SCRIPT_DIR")/../apk_cache}"
exec python3 "$SCRIPT_DIR/download_test_apks.py" --cache-dir "$CACHE" "$@"
