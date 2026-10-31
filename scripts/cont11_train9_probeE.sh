#!/usr/bin/env bash
# CONT-11 TRAIN-9 probe E — the CORRELATED map: deferred-branch positions
# (FIELD Lbt0;.L: recv=delegate oid, value=packed position) + the full
# LayoutNode graph (LN-DUMP Lel0; with the 512 bound: q=parent, J=delegate,
# f=index, h=bounds). Answers banked probe (a): walk the FAB ancestor chain
# and find the exact link whose placement value breaks.
set -u
cd /home/z/my-project
OUT=tmp/train9_probeE
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_FIELD_TRACE="Lbt0;.L"
export MINIANDROID_LAYOUTNODE_DUMP="Lel0;"
export MINIANDROID_LN_DUMP_LIMIT="512"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeE.log"
echo "exit=$?"
echo "=== deferred puts (.L) count ==="
grep "FIELD-TRACE.* put .*Lbt0;\.L" "$OUT/probeE.log" | grep -v "<init>" | wc -l
echo "=== node count ==="
grep -c "^\[LN-DUMP\] obj#" "$OUT/probeE.log"
