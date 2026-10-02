#!/bin/bash
# LOAD-AUDIT-2 — live runtime proofs of the P0 structural findings (opencalc, installed mode)
# Proves: P-1 getAbsolutePath hijack /tmp/miniandroid leak, P-3 AssetManager.open fake-success,
# P-2 FileOutputStream/openFileOutput absence, 3-run determinism, installed-identity provenance.
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
R=/home/z/my-project/run/audit
STORE=$R/store
QUAR=$R/quarantine
APK=/home/z/my-project/upload/opencalculator_53.apk
PKG=com.darkempire78.opencalculator
mkdir -p "$R" "$QUAR"

echo "===== 0. BINARY ====="
$B 2>&1 | head -3 || true

echo "===== 1. INSTALL ====="
rm -rf "$STORE"; mkdir -p "$STORE"
$B install "$APK" --data-root "$STORE" 2>&1 | tail -3
$B list-packages --data-root "$STORE" 2>&1 | tail -5
echo "installed base.apk sha256:"; sha256sum "$STORE"/data/app/$PKG/base.apk 2>/dev/null | cut -c1-16
echo "source apk sha256:";        sha256sum "$APK" | cut -c1-16
echo "store layout:"; ls "$STORE/data/data/$PKG" 2>/dev/null

echo "===== 2. HIDE SOURCE (mandatory installed-identity law) ====="
mv "$APK" "$QUAR/opencalculator_53.apk"
ls /home/z/my-project/upload/opencalculator_53.apk 2>&1 | tail -1

echo "===== 3. THREE RUNS FROM INSTALLED IDENTITY ONLY ====="
for i in 1 2 3; do
  OUT=$R/opencalc_r$i; rm -rf "$OUT"; mkdir -p "$OUT"
  MINIANDROID_FILE_IO=$OUT/file_io.jsonl MINIANDROID_GFX_PROVENANCE=1 \
    $B run --package $PKG --data-root "$STORE" -o "$OUT" --dump-api-trace >"$OUT/run.log" 2>&1
  echo "run$i rc=$? status=$(grep -oE 'Status: [A-Z_]+' $OUT/run.log | head -1) shot=$(sha256sum $OUT/screenshot.png 2>/dev/null | cut -c1-16)"
done

echo "===== 4. RESTORE SOURCE ====="
mv "$QUAR/opencalculator_53.apk" "$APK" && sha256sum "$APK" | cut -c1-16

echo "===== 5. P-1 getAbsolutePath HIJACK PROOF (file-IO paths containing /tmp/miniandroid) ====="
grep -h "tmp/miniandroid" $R/opencalc_r*/file_io.jsonl | head -5
echo "count: $(grep -h 'tmp/miniandroid' $R/opencalc_r*/file_io.jsonl | wc -l)"

echo "===== 6. P-3 ASSET OPEN FAKE-SUCCESS PROOF ====="
echo "-- asset OPENs recorded by the runtime:"
grep -ho 'OPEN [^ ]*assets/[^ "]*' $R/opencalc_r*/file_io.jsonl | sort | uniq -c
echo "-- assets actually present in installed base.apk:"
unzip -l "$STORE/data/app/$PKG/base.apk" 2>/dev/null | grep -oE 'assets/[A-Za-z0-9_./-]+' | sort -u
echo "-- any OPEN whose target is NOT in the APK = fake-success:"
for p in $(grep -ho 'OPEN [^ "]*assets/[A-Za-z0-9_./-]*' $R/opencalc_r*/file_io.jsonl | sed 's/^OPEN //' | sort -u); do
  base=$(echo "$p" | sed 's#.*@ apk=##;s#^assets/##')
  name=$(echo "$p" | grep -oE 'assets/[A-Za-z0-9_./-]+')
  if ! unzip -l "$STORE/data/app/$PKG/base.apk" 2>/dev/null | grep -q " $name\$"; then
    echo "FAKE-SUCCESS candidate: $name"
  fi
done

echo "===== 7. P-2 WRITE-PATH ABSENCE (api trace) ====="
for i in 1 2 3; do
  grep -oE '"(openFileOutput|openFileInput|FileOutputStream;|getAbsolutePath|deleteFile|fileList)[^"]*"[^}]*' $R/opencalc_r$i/api_calls.json 2>/dev/null | head -8
done
echo "-- any /data/user/0 string anywhere in traces (alias law probe):"
grep -h "data/user/0" $R/opencalc_r*/file_io.jsonl | head -3; echo "count: $(grep -h 'data/user/0' $R/opencalc_r*/file_io.jsonl 2>/dev/null | wc -l)"

echo "===== 8. 3-RUN DETERMINISM ====="
sha256sum $R/opencalc_r1/screenshot.png $R/opencalc_r2/screenshot.png $R/opencalc_r3/screenshot.png | cut -c1-16,65-
echo "PROOF DONE"
