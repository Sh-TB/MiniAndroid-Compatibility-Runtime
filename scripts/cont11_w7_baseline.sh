#!/bin/bash
# cont11_w7_baseline.sh — CONT-11 W7: dooz baseline + draw-window trace.
# Evidence-first: anchor, verdict, app_draw_ops, and the draw-window method
# sequence that shows where the compose draw chain dies.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w7
APK_ID=io.github.yamin8000.dooz

mkdir -p "$OUT"

echo "== baseline x3 =="
for i in 1 2 3; do
  RUN=$OUT/dooz_base$i
  rm -rf "$RUN"; mkdir -p "$RUN"
  timeout 300 "$BIN" run --package $APK_ID --data-root "$OUT/store_dooz" \
    --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
    > "$RUN/run.log" 2>&1
  echo "run$i rc=$?"
  grep -E "VERDICT|verdict" "$RUN/run.log" | head -2
  grep -E "APP_DRAW_OPS|app_ops=" "$RUN/run.log" | head -2
  if [ -f "$RUN"/*.png ]; then
    ls "$RUN"/*.png 2>/dev/null | head -1 | xargs -r sha256sum | cut -c1-16
  fi
done

echo "== draw-window trace run =="
RUN=$OUT/dooz_drawwin
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_DRAW_WINDOW_TRACE=1 timeout 300 "$BIN" run --package $APK_ID \
  --data-root "$OUT/store_dooz" --dump-view-tree --trace --max-seconds 120 \
  --frames 6 -o "$RUN" > "$RUN/run.log" 2>&1
echo "trace rc=$?"
grep -c "DRAWWIN-IN" "$RUN/run.log"
echo "-- Lt4 dispatch rows --"
grep -E "C013-ONDRAW" "$RUN/run.log" | head -6
echo "-- first 60 drawwin entries --"
grep "DRAWWIN-IN" "$RUN/run.log" | head -60
echo "-- last 30 drawwin entries --"
grep "DRAWWIN-IN" "$RUN/run.log" | tail -30
