#!/usr/bin/env bash
# cont46_post_fix_gate.sh — CONT-46 Phase-5 regression gate at the F-058-R
# binary a63bf3b53ac3c082: full anchors x3 + csw + probe battery + control.
set -uo pipefail
BASE=/home/z/my-project
OUT=$BASE/run/cont46
mkdir -p "$OUT"
cd "$BASE"

echo "== post-fix binary / head identity ==" | tee "$OUT/post_fix_gate.log"
sha256sum "$BASE/miniandroid/build/miniandroid" | tee -a "$OUT/post_fix_gate.log"
git -C "$BASE" rev-parse HEAD | tee -a "$OUT/post_fix_gate.log"

echo "== [1/2] canonical regression gate ==" | tee -a "$OUT/post_fix_gate.log"
bash "$BASE/scripts/cont37_regression.sh" >> "$OUT/post_fix_gate.log" 2>&1
echo "gate rc=$?" | tee -a "$OUT/post_fix_gate.log"

echo "== [2/2] skill self-test ==" | tee -a "$OUT/post_fix_gate.log"
python3 "$BASE/scripts/skill_selftest.py" > "$OUT/skill_selftest_post.log" 2>&1
echo "skill rc=$?" | tee -a "$OUT/post_fix_gate.log"

echo "POST-FIX-GATE-DONE" | tee -a "$OUT/post_fix_gate.log"
