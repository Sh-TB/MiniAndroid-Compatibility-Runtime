#!/usr/bin/env bash
# c7_w12_run_probe.sh — CODER7 WAVE-12 probe runner (the FGS-type /
# TaskStackBuilder / Intent-restart / PM-holding-permissions battery:
# ops W01..W13 over the c7.w12 fixture).
# Single-package run with the c7laws store (W12's ANY-law needs an
# INSTALLED second package holding c7.laws.OPEN). The service lifecycle
# (startForegroundService → onStartCommand) drains at the deterministic
# frame boundaries — W12Service rows then PlainService rows, FIFO.
#
# Usage: bash scripts/c7_w12_run_probe.sh <tag>
set -uo pipefail
R=/home/z/my-project/c7tree
BIN=${BIN:-$R/miniandroid/build/miniandroid}
TAG=${1:?tag}
OUT=$R/run/c7w12/$TAG
rm -rf "$OUT"; mkdir -p "$OUT"
STORE=$R/run/c7w12/store
rm -rf "$STORE"; mkdir -p "$STORE"
cp "$R"/fixtures/c7_laws_probe/c7laws.apk "$R"/fixtures/c7_laws_probe/c7laws_off.apk "$STORE/"
export MINIANDROID_PKG_STORE="$STORE"

# androguard cross-check of the W12 fixture (independent AXML truth:
# package, the typed service + its foregroundServiceType string, the
# parent chain, the type-less service)
python3 - "$R/fixtures/c7_w12_probe/c7w12.apk" <<'PY' \
    > "$OUT/androguard_check.json" 2> "$OUT/androguard_check.err"
import json, sys
import xml.etree.ElementTree as ET
from loguru import logger
logger.remove()
from androguard.core.apk import APK
a = APK(sys.argv[1])
root = ET.fromstring(a.get_android_manifest_axml().get_xml())
A = '{http://schemas.android.com/apk/res/android}'
pkg = root.get('package')
app = root.find('application')
acts = [x.get(A + 'name') for x in app.findall('activity')]
servs = [x.get(A + 'name') for x in app.findall('service')]
svc_types = {x.get(A + 'name'): x.get(A + 'foregroundServiceType')
             for x in app.findall('service')}
parents = {x.get(A + 'name'): x.get(A + 'parentActivityName')
           for x in app.findall('activity')}
perms = [p.get(A + 'name') for p in root.findall('uses-permission')]
ok = (pkg == 'c7.w12'
      and svc_types.get('.W12Service') in
          ('dataSync|location', '0x00000009')
      and svc_types.get('.PlainService') is None
      and parents.get('.MidAct') == '.RootAct'
      and parents.get('.ChildAct') == '.MidAct'
      and '.Main' in acts and '.RootAct' in acts
      and 'android.permission.INTERNET' in perms)
print(json.dumps({'all_ok': ok, 'package': pkg, 'activities': acts,
                  'services': servs, 'service_types': svc_types,
                  'parents': parents, 'permissions': perms}))
PY
echo "androguard_check rc=$? (0 = fixture contract holds)"
cat "$OUT/androguard_check.json"

for i in 1 2 3; do
  o="$OUT/cold$i"
  rm -rf "$o"; mkdir -p "$o"
  # fresh-install semantics: every run starts from an EMPTY app data dir
  # (the verdict file is MODE_APPEND — a stale dir would accumulate rows)
  rm -rf "$R/runtime/data/data/data/c7.w12"
  MINIANDROID_FILE_IO="$o/file_io.jsonl" \
  MINIANDROID_PKG_STORE="$STORE" \
  timeout 240 "$BIN" run "$R/fixtures/c7_w12_probe/c7w12.apk" \
    --width 1080 --height 1920 --frames 4 --max-seconds 90 -o "$o" \
    > "$o/run.log" 2>&1
  echo "run rc=$? -> $o"
  local_res="$R/runtime/data/data/data/c7.w12/files/c7w12_results.jsonl"
  [ -f "$local_res" ] && cp "$local_res" "$o/c7w12_results.jsonl"
done

echo '═══ verdict tallies (cold×3) ═══'
for i in 1 2 3; do
  d="$OUT/cold$i"
  echo "cold$i PASS=$(grep -c '|PASS|' $d/c7w12_results.jsonl 2>/dev/null) FAIL=$(grep -c '|FAIL|' $d/c7w12_results.jsonl 2>/dev/null)"
done
echo '═══ cold×3 row-identity check ═══'
for i in 2 3; do
  if diff -q "$OUT/cold1/c7w12_results.jsonl" "$OUT/cold$i/c7w12_results.jsonl" >/dev/null 2>&1; then
    echo "cold1 == cold$i (byte-identical)"
  else
    echo "cold1 != cold$i"; diff "$OUT/cold1/c7w12_results.jsonl" "$OUT/cold$i/c7w12_results.jsonl" | head -5
  fi
done
echo '═══ verdict rows (cold1) ═══'
cat "$OUT/cold1/c7w12_results.jsonl" 2>/dev/null
echo '═══ engine rows (cold1 file_io) ═══'
grep -hE 'SVC-FG-TYPE|PM-HOLDING-PERMS|C7-TSB|C7-INTENT-FACTORY|PI-SEND|C7-SVCINFO|C7-PHP' "$OUT/cold1/file_io.jsonl" 2>/dev/null | head -24
echo '═══ SHA-256 ═══'
sha256sum "$OUT"/cold*/c7w12_results.jsonl 2>/dev/null
echo "RUNNER DONE tag=$TAG"
