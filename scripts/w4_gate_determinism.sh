#!/bin/bash
# Wave-4 frame determinism gate: two runs per golden app, screenshot hash compare.
cd /home/z/my-project/miniandroid || exit 1
mkdir -p /tmp/gate
for apk in app.varlorg.unote_30 com.darkempire78.opencalculator_53 de.duenndns.gmdice_8; do
    for i in 1 2; do
        out="/tmp/gate/${apk}_run${i}"
        timeout 120 ./build/miniandroid run "/home/z/my-project/upload/canonical_apks/$apk.apk" -o "$out" --max-seconds 60 > "${out}.log" 2>&1
    done
    h1=$(sha256sum "/tmp/gate/${apk}_run1/screenshot.png" 2>/dev/null | cut -c1-12)
    h2=$(sha256sum "/tmp/gate/${apk}_run2/screenshot.png" 2>/dev/null | cut -c1-12)
    s1=$(grep -aoE "Status: [A-Z]+" "/tmp/gate/${apk}_run1.log" | head -1)
    s2=$(grep -aoE "Status: [A-Z]+" "/tmp/gate/${apk}_run2.log" | head -1)
    verdict=DIFF
    [ -n "$h1" ] && [ "$h1" = "$h2" ] && verdict=DETERMINISTIC
    echo "${apk}: run1=${h1:-none} (${s1}) run2=${h2:-none} (${s2}) => ${verdict}"
done
