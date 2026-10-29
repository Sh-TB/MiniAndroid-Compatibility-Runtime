#!/bin/bash
# CONT-11 W11 internet-train-7 car 9: trace the composed-factory arg
# evaluation — the caller chain of Lkr1;.a and the element ctor Ljr1;.<init>.
# train-6 F7 proved the element is BORN with garbage (viewConfiguration=
# CoroutineSingletons.COROUTINE_SUSPENDED, handler=Lpv; static no-op).
# Car-9 question: does the factory lambda ALREADY hold garbage in its
# captured fields at the call (upstream defect: composed-factory arg
# evaluation), or does the call-site arg pass corrupt (engine defect)?
# Probe: MINIANDROID_KR1_CALL_TRACE (S137b) — env-gated, inert otherwise.
set -u
cd /home/z/my-project
OUT=tmp/s137_run9
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_KR1_CALL_TRACE=1
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== KR1-CALL lines:"
grep 'KR1-CALL' "$OUT/throw_sites.log" | head -40
echo "=== count:"
grep -c 'KR1-CALL' "$OUT/throw_sites.log"
