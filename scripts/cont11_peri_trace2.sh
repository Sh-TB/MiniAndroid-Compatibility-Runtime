#!/bin/bash
# cont11_peri_trace2.sh — caller-frame trace of the $layout$1 ctor + layout
cd /home/z/my-project
STORE=run/cont11_census/store_app.simple.peri_983.apk
RUN=run/cont11_trace_peri2
rm -rf "$RUN"; mkdir -p "$RUN"
env MINIANDROID_CL_TRACE='Landroidx/compose/ui/node/LookaheadCapablePlaceable$layout$1;.<init>' \
  timeout 110 miniandroid/build/miniandroid run --package app.simple.peri \
  --data-root "$STORE" --max-seconds 60 --frames 4 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl.txt"
echo "rc=$?"
grep -c "CL-TRACE" "$RUN/cl.txt"
grep "CL-TRACE" "$RUN/cl.txt" | head -12 | cut -c1-230
