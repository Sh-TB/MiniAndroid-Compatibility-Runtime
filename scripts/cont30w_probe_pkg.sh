#!/usr/bin/env bash
# cont30w_probe_pkg.sh — repackage the fnew252 probe APK WITH its
# META-INF/services root entry (the w4 build script omitted it), then
# verify the current-main ServiceLoader law end-to-end.
# Discriminates: probe-packaging gap vs engine lookup defect.
set -euo pipefail
BASE=/home/z/my-project
FIX=$BASE/fixtures/fnew252_probe
WORK=$BASE/tmp/cont30w_probebuild
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont30w/f252_packed

rm -rf "$WORK" "$OUT"
mkdir -p "$WORK/pkg/META-INF/services" "$OUT"

# 1. copy the built APK and inject the fixture's services entry
cp "$WORK/../w4_probebuild/fnew252_probe/fnew252_probe.apk" "$WORK/svc.apk"
cp "$FIX"/META-INF/services/* "$WORK/pkg/META-INF/services/"
(cd "$WORK/pkg" && zip -q "$WORK/svc.apk" META-INF/services/*)
echo "packaged entries:"
unzip -l "$WORK/svc.apk" | rg "META-INF|dex|arsc"

# 2. run on the current binary
timeout 300 "$BIN" run "$WORK/svc.apk" --width 1080 --height 1920 \
  --frames 5 --max-seconds 15 -o "$OUT" > "$OUT/run.log" 2>&1
rc=$?
echo "rc=$rc"
rg -o "F252\|[A-Z0-9]+\|(PASS|FAIL)\|[^ ]*" "$OUT/run.log" | head -10
echo "--- S102 runtime trace:"
rg "S102-SERVICELOADER|S102-APK-ENTRY" "$OUT/run.log" | head -6
