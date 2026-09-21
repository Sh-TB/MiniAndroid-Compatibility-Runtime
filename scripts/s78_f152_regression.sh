#!/usr/bin/env bash
# s78_f152_regression.sh — S78 targeted regression for F-152 (+ F-154 depth chain).
#
# Laws under test (miniandroid/src/dex/dalvik_engine.cpp):
#   R-NEW-395: java.security.AccessController.doPrivileged MUST dispatch the
#              action's run() and return its result (libcore law). Pre-fix:
#              silent stub returned null → protobuf UnsafeUtil init stored
#              null Unsafe → F-152 NPE at Llt0;.w pc=808.
#   R-NEW-396: Class.getDeclaredFields on a SYNTHETIC class (Lsun/misc/Unsafe;)
#              answers the known declared-field subset (theUnsafe). Pre-fix:
#              0 fields → n12.run() scan found nothing → null.
#   R-NEW-397: Collections.EMPTY_SET/EMPTY_LIST/EMPTY_MAP static-final
#              singletons + Empty-family read dispatch (OpenJDK law). Pre-fix:
#              SGET-MISS null → Set.iterator() NPE at Lh3;.h pc=36 (F-154).
#
# Real-APK evidence (constitution: fixture success is not real-APK success):
# runs the canonical dooz v23 APK (the protobuf/DataStore consumer) and
# asserts the exception-signature DELTA on the engine diag log:
#   unsafeNPE (F-152): 9 (pre-fix)  → 0
#   setIterNPE (F-154): 8 (postfix2) → 0
#   [R-NEW-395] dispatch line present
#   [R-NEW-397] synthesized EMPTY_SET present
#   [R337-UNSAFE] real objectFieldOffset present (protobuf init works)
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
APK=$ROOT/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
OUT=$ROOT/run/s78_regression
mkdir -p "$OUT"

echo "[*] APK SHA256:"; sha256sum "$APK" | tee "$OUT/apk_sha256.txt"
MINIANDROID_F141_DIAG=1 timeout 280 "$ENG" run -o "$OUT/run" "$APK" \
    > "$OUT/engine.log" 2> "$OUT/diag.log"
rc=$?

diag="$OUT/diag.log"
unsafe_npe=$(rg -c "objectFieldOffset. on a null" "$diag" 2>/dev/null || echo 0)
setiter_npe=$(rg -c "Set;.iterator. on a null" "$diag" 2>/dev/null || echo 0)
r395=$(rg -c "\[R-NEW-395\] doPrivileged dispatched" "$diag" 2>/dev/null || echo 0)
r396=$(rg -c "\[R-NEW-396\] getDeclaredFields" "$diag" 2>/dev/null || echo 0)
r397=$(rg -c "\[R-NEW-397\] synthesized Collections.EMPTY_SET" "$diag" 2>/dev/null || echo 0)
unsafe_ok=$(rg -c "\[R337-UNSAFE\] objectFieldOffset" "$diag" 2>/dev/null || echo 0)

pass=0; fail=0
check() { # name value expected
  if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "  PASS  $1 = $2";
  else fail=$((fail+1)); echo "  FAIL  $1 = $2 (expected $3)"; fi
}
check "F-152 unsafeNPE count"        "$unsafe_npe"  "0"
check "F-154 setIterNPE count"       "$setiter_npe" "0"
# NOTE: >=1 — TWO protobuf UnsafeUtil init sites dispatch doPrivileged in
# dooz v23 (Llt0;.<clinit> + a second schema class); the law must fire for
# each. Zero is the failure mode this check guards (the silent stub).
[ "$r395" -ge 1 ] && { pass=$((pass+1)); echo "  PASS  R-NEW-395 doPriv dispatched ($r395 sites)"; } \
                     || { fail=$((fail+1)); echo "  FAIL  R-NEW-395 doPriv dispatched = $r395 (expected >=1)"; }
[ "$r396" -ge 1 ] && { pass=$((pass+1)); echo "  PASS  R-NEW-396 synthetic fields ($r396 sites)"; } \
                     || { fail=$((fail+1)); echo "  FAIL  R-NEW-396 synthetic fields = $r396 (expected >=1)"; }
check "R-NEW-397 EMPTY_SET seeded"   "$r397"        "1"
[ "$unsafe_ok" -ge 1 ] && { pass=$((pass+1)); echo "  PASS  R337-UNSAFE real offsets present ($unsafe_ok)"; } \
                     || { fail=$((fail+1)); echo "  FAIL  R337-UNSAFE real offsets absent"; }

python3 - "$OUT" <<'EOF'
import json, sys
out = sys.argv[1]
import subprocess
diag = out + "/diag.log"
def count(pat):
    r = subprocess.run(["rg", "-c", pat, diag], capture_output=True, text=True)
    return int(r.stdout.strip()) if r.returncode == 0 else 0
json.dump({
  "wave": "S78", "target": "F-152 depth chain (R-NEW-395/396/397)",
  "apk": "io.github.yamin8000.dooz_23.apk",
  "unsafe_npe_f152": count(r"objectFieldOffset\. on a null"),
  "setiter_npe_f154": count(r"Set;\.iterator\(\) on a null"),
  "r395_dispatch": count(r"\[R-NEW-395\] doPrivileged dispatched"),
  "r396_synthetic_fields": count(r"\[R-NEW-396\] getDeclaredFields"),
  "r397_empty_set": count(r"\[R-NEW-397\] synthesized Collections\.EMPTY_SET"),
  "r337_unsafe_offsets": count(r"\[R337-UNSAFE\] objectFieldOffset"),
}, open(out + "/regression.json", "w"), indent=1)
EOF

echo "F152-REGRESSION RESULT: $pass pass, $fail fail (rc=$rc)"
[ "$fail" = "0" ]
