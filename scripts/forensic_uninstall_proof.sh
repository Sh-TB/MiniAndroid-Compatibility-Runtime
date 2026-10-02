#!/bin/bash
# UNINSTALL SEMANTICS proof — completes the recorded PENDING row
# (F-NEW-231 "Uninstall command | PENDING"). Generic store-level proof:
# two packages, uninstall one, the other must stay byte-identical.
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
PROBE_APK=/home/z/my-project/run/audit/loading_probe.apk
OC_APK=/home/z/my-project/run/audit/regression/store_opencalc/data/app/com.darkempire78.opencalculator/base.apk
S=/home/z/my-project/run/forensic_uninstall_store
rm -rf "$S"; mkdir -p "$S"
fails=0; chk(){ if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 (got=$2 want=$3)"; fails=$((fails+1)); fi; }

# 1. install two packages
$B install "$PROBE_APK" --data-root "$S" >/dev/null 2>&1; chk "install probe rc" "$?" "0"
$B install "$OC_APK"  --data-root "$S" >/dev/null 2>&1; chk "install opencalc rc" "$?" "0"
# 2. both visible
n=$($B list-packages --data-root "$S" 2>/dev/null | grep -c "^  {\"package\""); chk "two packages visible" "$n" "2"
# 3. create data for both (simulated state: files under data/data/<pkg>)
mkdir -p "$S/data/data/com.probe.loading/files" "$S/data/data/com.darkempire78.opencalculator/files"
echo state-A > "$S/data/data/com.probe.loading/files/a.txt"
echo state-B > "$S/data/data/com.darkempire78.opencalculator/files/b.txt"
mkdir -p "$S/storage/emulated/0/Android/data/com.darkempire78.opencalculator/cache"
echo cache > "$S/storage/emulated/0/Android/data/com.darkempire78.opencalculator/cache/c.bin"
# 4. uninstall opencalc
out=$($B uninstall --package com.darkempire78.opencalculator --data-root "$S" 2>/dev/null); rc=$?
chk "uninstall opencalc rc" "$rc" "0"
echo "$out" | grep -q '"uninstall": "SUCCESS"'; chk "uninstall verdict SUCCESS" "$?" "0"
# 5. opencalc trees gone; probe intact
[ ! -e "$S/data/app/com.darkempire78.opencalculator" ]; chk "codePath removed" "$?" "0"
[ ! -e "$S/data/data/com.darkempire78.opencalculator" ]; chk "internalData removed" "$?" "0"
[ ! -e "$S/storage/emulated/0/Android/data/com.darkempire78.opencalculator" ]; chk "externalData removed" "$?" "0"
[ -f "$S/data/data/com.probe.loading/files/a.txt" ]; chk "probe data intact" "$?" "0"
[ -f "$S/data/app/com.probe.loading/base.apk" ]; chk "probe codePath intact" "$?" "0"
n=$($B list-packages --data-root "$S" 2>/dev/null | grep -c "^  {\"package\""); chk "one package remains" "$n" "1"
# 6. NOT_INSTALLED honesty
$B uninstall --package com.darkempire78.opencalculator --data-root "$S" >/dev/null 2>&1; chk "second uninstall NOT_INSTALLED rc" "$?" "2"
# 7. reinstall -> clean namespace (data/data absent until a run creates it)
$B install "$OC_APK" --data-root "$S" >/dev/null 2>&1; chk "reinstall opencalc rc" "$?" "0"
[ ! -e "$S/data/data/com.darkempire78.opencalculator/files/b.txt" ]; chk "reinstall = clean namespace" "$?" "0"
# 8. uninstall probe + opencalc -> store empty
$B uninstall --package com.probe.loading --data-root "$S" >/dev/null 2>&1; chk "uninstall probe rc" "$?" "0"
$B uninstall --package com.darkempire78.opencalculator --data-root "$S" >/dev/null 2>&1
n=$($B list-packages --data-root "$S" 2>/dev/null | grep -c "^  {\"package\""); chk "store empty" "$n" "0"
echo "UNINSTALL-PROOF-GATE: $([ $fails = 0 ] && echo ALL PASS || echo "$fails FAIL")"
exit $fails
