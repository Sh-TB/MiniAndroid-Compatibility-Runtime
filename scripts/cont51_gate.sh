#!/usr/bin/env bash
# cont51_gate.sh — CONT-51 zero-drift regression gate at the F-NEW-322/323
# fix binary. Canonical anchors x3 (cont37_regression.sh), csw target x3,
# simplecalc control x3, support group (BMI/alex/notes) x3, the two new
# probes (fnew322 5 rows, fnew323 6 rows) x3, and the CONT-50 probe
# rebuilds (fnew320 shadowing+computeScroll, fnew309 LP generation).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont51/gate
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)" | tee "$OUT/gate.log"

echo "== [1/6] canonical anchors + csw + control (cont37_regression.sh) ==" | tee -a "$OUT/gate.log"
bash "$BASE/scripts/cont37_regression.sh" all > "$OUT/cont37_full.log" 2>&1
grep -E "^REG|^PROBE|^F298" "$OUT/cont37_full.log" | tee -a "$OUT/gate.log"
echo "cont37 rc=$?" | tee -a "$OUT/gate.log"

echo "== [2/6] support group x3 (BMI/alex/notes) ==" | tee -a "$OUT/gate.log"
BMI=$BASE/upload/cont11_apks/bmi_402.apk
ALEX=$BASE/upload/cont11_apks/alexcalc_20.apk
NOTES=$BASE/upload/notes_secuso_105.apk
# discover the exact pinned APKs (CONT-50 recorded b52252c2de19b03a /
# c8d69f811b23f245 / eb5ebd559cad1028)
ls "$BASE/upload/cont47_apks/" 2>/dev/null | tee -a "$OUT/gate.log"

run1() {
  local label="$1" apk="$2" want="${3:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local verdict="DRIFT"
  [ "$sha" = "$want" ] && verdict="MATCH"
  echo "REG $label rc=$rc sha=$sha want=$want $verdict" | tee -a "$OUT/gate.log"
}

for i in 1 2 3; do
  run1 "bmi_r$i"      "$BMI"   b52252c2de19b03a
  run1 "alex_r$i"     "$ALEX"  c8d69f811b23f245
  run1 "notes_r$i"    "$NOTES" eb5ebd559cad1028
done

echo "== [3/6] fnew322/fnew323 probes x3 ==" | tee -a "$OUT/gate.log"
for i in 1 2 3; do
  for p in fnew322 fnew323; do
    o="$OUT/${p}_r$i"; rm -rf "$o"; mkdir -p "$o"
    timeout 300 "$BIN" run "$BASE/run/cont51/${p}_probe.apk" --width 1080 --height 1920 \
      --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
    pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
    fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
    echo "PROBE ${p}_r$i PASS=$pass FAIL=$fail" | tee -a "$OUT/gate.log"
  done
done

echo "== [4/6] CONT-50 probe rebuilds (fnew320, fnew309) ==" | tee -a "$OUT/gate.log"
bash "$BASE/scripts/cont50_build_probe.sh" > "$OUT/f320_build.log" 2>&1 \
  && echo "fnew320 probe built: $(sha256sum $BASE/run/cont50/fnew320_probe.apk | cut -c1-16)" | tee -a "$OUT/gate.log" \
  || echo "fnew320 BUILD FAILED" | tee -a "$OUT/gate.log"
ls "$BASE"/scripts/ | grep -i "309" | tee -a "$OUT/gate.log"

echo "GATE-DONE" | tee -a "$OUT/gate.log"
