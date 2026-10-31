#!/usr/bin/env bash
# CONT-11 TRAIN-9 (fix train) probe C — the FAB ancestor chain walk.
# LN-DUMP Lel0; (LayoutNode graph: parent refs + sizes) with the new
# read-only bound knob MINIANDROID_LN_DUMP_LIMIT=512 so late-allocated
# nodes (FAB family obj#12222/12223) are reachable. One-hop expansion for
# the first 8 dumped nodes names the referenced classes (coordinator ids).
set -u
cd /home/z/my-project
OUT=tmp/train9_probeC
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_LAYOUTNODE_DUMP="Lel0;"
export MINIANDROID_LN_DUMP_LIMIT="512"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeC.log"
echo "exit=$?"
echo "=== LayoutNode dump lines ==="
grep -c "LN-DUMP" "$OUT/probeC.log"
echo "=== nodes holding a 409-wide child (the FAB wrap family) ==="
grep "LN-DUMP" "$OUT/probeC.log" | grep "12223\|12222\|12247" | head -6
echo "=== last 12 dump lines (late-allocated nodes) ==="
grep "LN-DUMP" "$OUT/probeC.log" | tail -12
