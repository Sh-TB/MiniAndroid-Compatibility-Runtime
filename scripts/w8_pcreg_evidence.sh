#!/bin/bash
# w8_pcreg_evidence.sh — F-NEW-521 wave: runtime register evidence at the
# Lhv0;.d growth-decision branch (eu pcs 0x84/0x88/0x9c/0xaa).
# Evidence-first: reproduce the dooz baseline, then watch the branch.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w8
APK_ID=io.github.yamin8000.dooz

mkdir -p "$OUT"

echo "== install dooz into store =="
[ -d "$OUT/store_dooz/data/app/io.github.yamin8000.dooz" ] || \
  timeout 300 "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" \
    --data-root "$OUT/store_dooz" 2>&1 | tail -2
[ -d "$OUT/store_dooz_pcreg/data/app/io.github.yamin8000.dooz" ] || \
  timeout 300 "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" \
    --data-root "$OUT/store_dooz_pcreg" 2>&1 | tail -2

echo "== baseline x3 (no diag) =="
for i in 1 2 3; do
  RUN=$OUT/dooz_base$i
  rm -rf "$RUN"; mkdir -p "$RUN"
  timeout 400 "$BIN" run --package $APK_ID --data-root "$OUT/store_dooz" \
    --dump-view-tree --trace --max-seconds 300 --frames 40 -o "$RUN" \
    > "$RUN/run.log" 2>&1
  echo "run$i rc=$?"
  grep -E "VERDICT|verdict" "$RUN/run.log" | head -2
  PNG=$(ls "$RUN"/*.png 2>/dev/null | head -1)
  [ -n "$PNG" ] && sha256sum "$PNG" | cut -c1-16
done

echo "== PC-WATCH register evidence run =="
RUN=$OUT/dooz_pcreg
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_PC_WATCH='Lhv0;.d:0x84,Lhv0;.d:0x88,Lhv0;.d:0x9c,Lhv0;.d:0xaa' \
  timeout 400 "$BIN" run --package $APK_ID --data-root "$OUT/store_dooz_pcreg" \
  --dump-view-tree --trace --max-seconds 300 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2>&1
echo "watch rc=$?"
echo "-- PC-WATCH rows (first 80) --"
grep "PC-WATCH" "$RUN/run.log" | head -80
echo "-- PC-WATCH total --"
grep -c "PC-WATCH" "$RUN/run.log"
echo "-- 0xaa (growth region entries) --"
grep "PC-WATCH.*:aa " "$RUN/run.log" | head -10
