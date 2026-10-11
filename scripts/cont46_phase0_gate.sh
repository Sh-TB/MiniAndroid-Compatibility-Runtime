#!/usr/bin/env bash
# cont46_phase0_gate.sh — CONT-46 Phase-0 baseline gate at HEAD 8f2f6aab,
# binary 56c045260767ac66 (rebuilt from the true remote lineage).
# Anchors x3, csw target x3, probe battery, simplecalc control x3,
# then Skill self-test. All output under run/cont46/.
set -uo pipefail
BASE=/home/z/my-project
OUT=$BASE/run/cont46
mkdir -p "$OUT"
cd "$BASE"

echo "== binary / head identity ==" | tee "$OUT/phase0_gate.log"
sha256sum "$BASE/miniandroid/build/miniandroid" | tee -a "$OUT/phase0_gate.log"
git -C "$BASE" rev-parse HEAD | tee -a "$OUT/phase0_gate.log"

echo "== [1/2] canonical regression gate ==" | tee -a "$OUT/phase0_gate.log"
bash "$BASE/scripts/cont37_regression.sh" >> "$OUT/phase0_gate.log" 2>&1
echo "gate rc=$?" | tee -a "$OUT/phase0_gate.log"

echo "== [2/2] skill self-test ==" | tee -a "$OUT/phase0_gate.log"
python3 "$BASE/scripts/skill_selftest.py" > "$OUT/skill_selftest.log" 2>&1
echo "skill rc=$?" | tee -a "$OUT/phase0_gate.log"
grep -cE "^PASS" "$OUT/skill_selftest.log" | xargs -I{} echo "skill PASS lines: {}" | tee -a "$OUT/phase0_gate.log"
grep -cE "^FAIL" "$OUT/skill_selftest.log" | xargs -I{} echo "skill FAIL lines: {}" | tee -a "$OUT/phase0_gate.log"

echo "PHASE0-GATE-DONE" | tee -a "$OUT/phase0_gate.log"
