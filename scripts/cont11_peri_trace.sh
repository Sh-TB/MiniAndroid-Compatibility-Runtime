#!/bin/bash
# cont11_peri_trace.sh — trace $placementBlock field stores on peri's Compose run
cd /home/z/my-project
STORE=run/cont11_census/store_app.simple.peri_983.apk
RUN=run/cont11_trace_peri
rm -rf "$RUN"; mkdir -p "$RUN"
env MINIANDROID_FIELD_TRACE='Landroidx/compose/ui/node/LookaheadCapablePlaceable$layout$1;.$placementBlock' \
  timeout 110 miniandroid/build/miniandroid run --package app.simple.peri \
  --data-root "$STORE" --max-seconds 60 --frames 4 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/ft.txt"
echo "rc=$?"
grep -c "placementBlock" "$RUN/ft.txt"
grep "placementBlock" "$RUN/ft.txt" | head -8 | cut -c1-200
