#!/bin/bash
# working_vs_failing_probe.sh — LOADING-CAMPAIGN regression gate.
# Re-runs the working goldens from their installed stores and compares the
# screenshot SHA-256 (first 16 hex) against the recorded golden. A generic
# fix that drifts ANY golden fails the gate.
set -uo pipefail
B=/home/z/my-project/miniandroid/build/miniandroid
REG=/home/z/my-project/run/audit/regression
mkdir -p "$REG"

# name | package | golden_sha | runs
TARGETS=(
  "opencalc|com.darkempire78.opencalculator|e364b001ee7abd66|3"
  "chess|jwtc.android.chess|b5a7a35d5fe0564b|3"
  "dooz|io.github.yamin8000.dooz|d602648e8e401895|3"
  "microtimer|dubrowgn.microtimer|da73010a37dd0189|3"
  "unote|app.varlorg.unote|4f1a9e4e8f64fae8|3"
)

fails=0
for t in "${TARGETS[@]}"; do
  IFS='|' read -r name pkg golden runs <<< "$t"
  st="$REG/store_$name"
  if [ ! -d "$st/data/app/$pkg" ]; then
    echo "FAIL  $name — store missing (install first)"; fails=$((fails+1)); continue
  fi
  shas=""
  ok=1
  for i in $(seq 1 "$runs"); do
    OUT=$REG/${name}_gate_r$i; rm -rf "$OUT"; mkdir -p "$OUT"
    MINIANDROID_FILE_IO=$OUT/file_io.jsonl \
      $B run --package "$pkg" --data-root "$st" -o "$OUT" >"$OUT/run.log" 2>&1
    s=$(sha256sum "$OUT/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
    [ "$s" = "$golden" ] || ok=0
  done
  [ "$ok" = "1" ] && echo "PASS  $name == $golden x$runs ($shas)" \
                  || { echo "FAIL  $name drifted: got$shas want $golden"; fails=$((fails+1)); }
done
echo "WORKING-VS-FAILING-GATE: $([ $fails = 0 ] && echo ALL PASS || echo "$fails FAIL")"
exit $fails
