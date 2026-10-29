#!/bin/bash
# CONT-11 W10 internet-train-6 car 5: trace INSIDE Ls;.h0 (JobSupport.start /
# CoroutineStart.invoke inlined). Static law says: block (Lru;) IS Lne; (Base-
# ContinuationImpl via Lru;->Lir1;->Lnq;->Lne;) so the UNDISPATCHED arm must call
#   Lxz1;.k(...) then Lj90;.h(block, receiver, completion)  == DIRECT body invoke.
# If instead Ltl;.V appears -> instance-of walked the wrong hierarchy.
# If NOTHING appears -> h0 never ran (death earlier: Lkp1;.<init> or Lxz1;.I tail).
set -u
cd /home/z/my-project
OUT=tmp/s137_run5
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Ls;|h0'
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== invokes inside Ls;.h0 frames:"
grep 'INVOKE-TARGET' "$OUT/throw_sites.log" | head -40
grep -c 'INVOKE-TARGET' "$OUT/throw_sites.log"
