#!/usr/bin/env bash
# s133_fix_suite.sh — run all 14 control fixtures through the harness APK,
# tap-driven (--tap center@3), with screenshot forensics per test.
set -uo pipefail
ROOT=/home/z/my-project
RUN=$ROOT/run/s133/fixsuite
APK=$ROOT/upload/s133_webfix/build/webfix_v1.0_vc1.apk
OUT=$ROOT/evidence/s133_webfix
mkdir -p "$RUN" "$OUT"

declare -A TAPS=(
  [T01]="270,63"   [T02]="810,63"
  [T03]="270,189"  [T04]="810,189"
  [T05]="270,315"  [T06]="810,315"
  [T07]="270,441"  [T08]="810,441"
  [T09]="270,567"  [T10]="810,567"
  [T11]="270,693"  [T12]="810,693"
  [T13]="270,819"  [T14]="810,819"
)
ORDER=(T01 T02 T03 T04 T05 T06 T07 T08 T09 T10 T11 T12 T13 T14)

for t in "${ORDER[@]}"; do
  dir="$RUN/$t"
  mkdir -p "$dir"
  echo "=== $t ==="
  timeout 150 "$ROOT/miniandroid/build/miniandroid" run -o "$dir" \
    --max-seconds 15 --tap "${TAPS[$t]}@3" "$APK" > "$dir/run.log" 2>&1
  echo "  exit=$? frames=$(grep -c 'Frame' "$dir/run.log" 2>/dev/null || echo '?')"
  python3 "$ROOT/scripts/s133_screen_forensics.py" "$dir/screenshot.png" \
    --json "$dir/screen_metrics.json" > /dev/null 2>&1 \
    && python3 - "$dir" "$t" << 'PY'
import json, sys
d = json.load(open(sys.argv[1] + "/screen_metrics.json"))
top = ", ".join(f"{c['rgb']}" for c in d["top_colors"][:4])
print(f"  {sys.argv[2]}: class={d['classification']} unique={d['unique_colors']} "
      f"nonwhite={d['non_white_pixels']} entropy={d['entropy_bits']}")
print(f"    top colors: {top}")
PY
done
echo "SUITE COMPLETE → $RUN"
