#!/usr/bin/env bash
# s105_park_probe_check.sh — ROOT-010 WORKER-PARK-DEPTH probe gate.
#
# Builds nothing; asserts the deterministic park/idle law on a run dir
# produced by:
#   miniandroid run --execution-mode real-dalvik --frames 6 \
#     --frame-delay 1500 --dump-view-tree -o <dir> <park_probe.apk>
#
# Law claims asserted (fixtures/s105_park_probe/src/com/probe/s105park/
# ParkProbeActivity.java documents the modelled kotlinx Worker.runLoop):
#   A. rc == 0 (no F084 halt, no crash-driven exit)
#   B. no [HALT-LOOP] in the engine log (no infinite worker spin)
#   C. >=1 [PARK-YIELD] with depth=1 (worker reached idle park and the
#      frame chain suspended at the drain boundary)
#   D. task1 executed EXACTLY once  (text "executed=1" appears once)
#   E. task2 executed EXACTLY once  (text "executed=2" appears once)
#   F. final on-screen state shows parks >= 1 (idle-park leg exercised)
#   G. exactly one park/rescan per boundary family — the same-boundary
#      8-slice re-pop artifact is gone (resumed=1, not resumed=8)
#
# Usage: bash scripts/s105_park_probe_check.sh <run_dir> [rc]
set -uo pipefail
DIR="${1:?usage: s105_park_probe_check.sh <run_dir> [rc]}"
RC="${2:-0}"
fails=0
chk() { # chk <desc> <ok>
  if [ "$2" = "1" ]; then echo "PASS  $1"; else echo "FAIL  $1"; fails=$((fails+1)); fi
}
[ "$RC" = "0" ] && ok=1 || ok=0
chk "A rc==0" "$ok"
grep -q "HALT-LOOP" "$DIR/engine.log" && ok=0 || ok=1
chk "B no HALT-LOOP (no worker spin)" "$ok"
grep -q "PARK-YIELD.*depth=1" "$DIR/engine.log" && ok=1 || ok=0
chk "C worker park yield at depth=1" "$ok"
n=$(grep -o 'text="executed=1 parks=[0-9]* running=true last=task1"' "$DIR/engine.log" | wc -l)
[ "$n" -ge 1 ] && ok=1 || ok=0
chk "D task1 executed (visible)" "$ok"
n=$(grep -o 'last=task1' "$DIR/engine.log" | sort -u | wc -l); [ "$n" = "1" ] && ok=1 || ok=0
chk "D' task1 exactly-once key" "$ok"
n=$(grep -o 'last=task2' "$DIR/engine.log" | sort -u | wc -l); [ "$n" = "1" ] && ok=1 || ok=0
chk "E task2 exactly-once (woken once)" "$ok"
grep -o 'executed=2 parks=[0-9]*' "$DIR/engine.log" | grep -oE 'parks=[0-9]+' | awk -F= '{exit !($2>=1)}' && ok=1 || ok=0
chk "F idle-park leg exercised (parks>=1)" "$ok"
grep -q "resumed=8" "$DIR/engine.log" && ok=0 || ok=1
chk "G one rescan per boundary (no 8-pop artifact)" "$ok"
echo "S105-PARK-PROBE: $([ $fails = 0 ] && echo ALL PASS || echo "$fails FAIL")"
exit $fails
