#!/usr/bin/env bash
# SHIM — canonical version lives in the repo:
#   MiniAndroid-Compatibility-Runtime/scripts/build_fixture_apk.sh
# This outer copy previously diverged (it passed a bare directory to D8,
# which D8 8.3.37 rejects, and lacked the aapt2 resource path). One
# canonical builder only (campaign §29); never edit this shim.
exec bash "$(dirname "$0")/../MiniAndroid-Compatibility-Runtime/scripts/build_fixture_apk.sh" "$@"
