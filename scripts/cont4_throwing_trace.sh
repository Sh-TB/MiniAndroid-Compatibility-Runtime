#!/usr/bin/env bash
# cont4_throwing_trace.sh — run fairymahjong repeatedly until a THROWING
# (flower-board) run is captured WITH full METHOD-TRACE of Lm2;.b.
# The game's default board roll is nondeterministic (16x4 / 17x4 / 72-tile
# flower variants observed); only the flower variant reaches the ISE.
set -uo pipefail
cd /home/z/my-project/miniandroid
OUTBASE=/home/z/my-project/run/cont4
MAXRUNS=${1:-6}
for i in $(seq 1 "$MAXRUNS"); do
  D="$OUTBASE/trace_run$i"
  echo "=== RUN $i -> $D"
  MINIANDROID_METHOD_TRACE='Lm2;|b' \
  MINIANDROID_METHOD_TRACE_BUDGET=200000 \
  MINIANDROID_CONT4_SOLVER_DIAG=1 \
  timeout 900 ./build/miniandroid run -o "$D" \
    ../apk_cache/com.fairytrick.fairymahjong_5.apk \
    --max-instructions 200000000 \
    > "$D.out" 2> "$D.err"
  RC=$?
  BOARD=$(grep -o "pc=0x51b (visit 1).*" "$D.err" | head -1 | grep -o "v9=i[0-9]*" | head -1)
  THROW=$(grep -c "Even face counts" "$D.err" || true)
  LINES=$(grep -c "METHOD-TRACE" "$D.err" || true)
  echo "run$i rc=$RC board=($BOARD) throw_hits=$THROW trace_lines=$LINES"
  if [ "$THROW" -gt 0 ]; then
    echo "THROWING RUN CAPTURED: $D"
    exit 0
  fi
done
echo "NO THROWING RUN IN $MAXRUNS ATTEMPTS"
exit 1
