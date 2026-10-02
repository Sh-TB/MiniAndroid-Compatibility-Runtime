#!/bin/bash
# IAPK AFTER campaign — per-package filesystem law (F-NEW-234) proof suite.
# Sources are physically quarantined during ALL installed runs.
set -u
cd /home/z/my-project
B=miniandroid/build/miniandroid
STORE=run/iapk/store2
EV=run/iapk/after
mkdir -p "$EV" run/iapk/quarantine

# SHA helper
sha() { sha256sum "$1" | cut -c1-16; }

echo "=== STATE B: store2 manifest (post-install, pre-launch) ==="
python3 scripts/iapk_manifest.py "$STORE::STORE2" --json "$EV/state_B_store2.json" --tree "$EV/state_B_store2.txt" >/dev/null 2>&1

# The 4 source APKs were moved to run/iapk/quarantine before any launch.
echo "=== QUARANTINE CHECK: source APKs must NOT be at their original paths ==="
for f in upload/opencalculator_53.apk upload/canonical_apks/bouncy.apk upload/telegram_official.apk upload/chess_jwtc_298.apk; do
  [ -e "$f" ] && echo "FAIL: $f still visible" || echo "HIDDEN: $f"
done | tee "$EV/quarantine_check.txt"

run_pkg() {  # run_pkg <package> <label> <run#>
  local PKG=$1 LABEL=$2 N=$3
  local OUT="$EV/${LABEL}_r$N"
  mkdir -p "$OUT"
  MINIANDROID_FILE_IO="$OUT/file_io.jsonl" MINIANDROID_GFX_PROVENANCE="$OUT/gfx_provenance.json" \
    timeout 900 $B run --package "$PKG" --data-root "$STORE" -o "$OUT" \
    > "$OUT/stdout.log" 2> "$OUT/stderr.log"
  echo "$LABEL r$N rc=$?"
  grep -m1 "Status:" "$OUT/stdout.log" || true
  if [ -f "$OUT/screenshot.png" ]; then echo "  shot=$(sha "$OUT/screenshot.png")"; fi
}

echo "=== RUNS x3 (installed identity only) ==="
for N in 1 2 3; do
  run_pkg com.darkempire78.opencalculator opencalc $N
  run_pkg com.dozingcatsoftware.bouncy bouncy $N
  run_pkg jwtc.android.chess chess $N
done
echo "(telegram runs happen separately — long)"

echo "=== STATE C: store2 manifest after all launches ==="
python3 scripts/iapk_manifest.py "$STORE::STORE2" --json "$EV/state_C_store2.json" --tree "$EV/state_C_store2.txt" >/dev/null 2>&1
python3 - << 'EOF'
import json, sys
sys.path.insert(0, 'scripts')
from iapk_manifest import diff_snap
a = json.load(open('run/iapk/after/state_B_store2.json'))
b = json.load(open('run/iapk/after/state_C_store2.json'))
d = diff_snap(a, b)
print(f"CREATED={d['created_count']} MODIFIED={d['modified_count']} DELETED={d['deleted_count']}")
print("-- CREATED paths --")
for p in d['INSTALL_OR_LAUNCH_CREATED'][:40]:
    print("  +", p.replace('run/iapk/store2/', ''))
json.dump(d, open('run/iapk/after/state_diff_B_C.json', 'w'), indent=1)
EOF
echo "IAPK-AFTER suite done"
