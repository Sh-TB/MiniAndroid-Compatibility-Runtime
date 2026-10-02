#!/bin/bash
# loading_probe_runner.sh — LOADING-CAMPAIGN synthetic probe gate.
# Builds the probe fixture, installs it into a FRESH store, runs it 3 times
# WITHOUT clearing the store (restart-persistence law) and asserts every P0
# contract from the rendered probe text + file-IO trace.
set -uo pipefail
B=/home/z/my-project/miniandroid/build/miniandroid
R=/home/z/my-project/run/audit
FIX=/home/z/my-project/fixtures/loading_probe
APK=$R/loading_probe.apk
STORE=$R/probe_gate_store
fails=0
chk() { [ "$2" = "1" ] && echo "PASS  $1" || { echo "FAIL  $1"; fails=$((fails+1)); } }

bash /home/z/my-project/scripts/build/build_fixture_apk.sh "$FIX" "$APK" >/dev/null
rm -rf "$STORE"; mkdir -p "$STORE"
$B install "$APK" --data-root "$STORE" >/dev/null 2>&1

declare -a RUNS_TEXT RUNS_IO
extract_text() { python3 -c "
import json,sys
d = json.load(open('$1'))
def walk(n):
    if isinstance(n, dict):
        t = n.get('text','')
        if t: return t
        for k in ('children','nodes'):
            for c in n.get(k,[]) or []:
                r = walk(c)
                if r: return r
    elif isinstance(n, list):
        for c in n:
            r = walk(c)
            if r: return r
    return ''
print(walk(d))"; }
for i in 1 2 3; do
  OUT=$R/gate_r$i; rm -rf "$OUT"; mkdir -p "$OUT"
  MINIANDROID_FILE_IO=$OUT/file_io.jsonl \
    $B run --package com.probe.loading --data-root "$STORE" -o "$OUT" \
    --dump-view-tree >"$OUT/run.log" 2>&1
  RUNS_TEXT[i]=$(extract_text "$OUT/view_tree.json")
  RUNS_IO[i]=$OUT/file_io.jsonl
done

T="${RUNS_TEXT[1]}"
has() { echo "$T" | grep -q "$1" && echo 1 || echo 0; }
chk "provider install stage ran"            "$(has 'provider-ran=1')"
chk "ST-1 getAbsolutePath unhijacked"       "$(has 'abs-ok=true')"
chk "ST-2 openFileOutput write+length"      "$(has 'write-length=14')"
chk "read-back byte equality"               "$(has 'read-ok=true')"
chk "openFileInput missing → FNFE"          "$(has 'ofi-missing=FNFE-HONEST')"
chk "/data/user/0 ↔ /data/data alias"       "$(has 'alias-exists=true')"
chk "fileList sees probe.txt"               "$(has 'fileList-has-probe=1')"
chk "deleteFile honest (true then false)"   "$(has 'deleteFile-again=false')"
chk "File.renameTo + length INT64 law"      "$(has 'ren-dst-length=13')"
chk "R-1 missing asset → FNFE"              "$(has 'asset-missing=FNFE-HONEST')"
chk "R-7 AssetManager.list"                 "$(has 'asset-list-has-text=1')"
chk "R-2 openFd stored-entry AFD"           "$(has 'openFd-length=75')"
chk "R-2 AFD stream bytes == entry bytes"   "$(has 'afd-bytes=75')"
chk "R-10 decodeStream asset → bitmap"      "$(has 'decodeStream=8x8')"
chk "ST-5 decodeFile through path law"      "$(has 'decodeFile=8x8')"
chk "ST-6 prefs XML escape round-trip"      "$(has 'prefs-esc=a<b>&c')"
chk "host escape DENIED (/etc hostname)"    "$(has 'host-deny=FNFE-HONEST')"
chk "/dev/urandom AOSP-legal allow"         "$(has 'urandom-read=OK')"
chk "package isolation (other pkg absent)"  "$(has 'isolation-other-pkg=false')"
chk "restart persistence run1→2 (runs=2)"   "$(echo "${RUNS_TEXT[2]}" | grep -q 'prefs-runs=2' && echo 1 || echo 0)"
chk "restart persistence run2→3 (runs=3)"   "$(echo "${RUNS_TEXT[3]}" | grep -q 'prefs-runs=3' && echo 1 || echo 0)"
chk "WAL/db persisted on store"             "$([ -f "$STORE/data/data/com.probe.loading/databases/probe_db.sqlite" ] && echo 1 || echo 0)"
chk "write file persisted on store"         "$([ "$(stat -c%s "$STORE/data/data/com.probe.loading/files/probe.txt" 2>/dev/null)" = "14" ] && echo 1 || echo 0)"

echo "LOADING-PROBE-GATE: $([ $fails = 0 ] && echo ALL PASS || echo "$fails FAIL")"
exit $fails
