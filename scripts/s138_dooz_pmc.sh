#!/usr/bin/env bash
# S138 train (dooz click-detection chain): PMC probe on the pointerInput
# construction law. s135/train-7 car-9..11: the REAL pointerInput element
# (Ljr1; with wv1.z/y keys + Lj6; handler) is constructed statically inside
# Lpm;.c (pc 0x0db6/0x0e04) but NEVER dynamically. The PMC watchlist logs
# ENTER + every invoke inside the watched methods, so the last logged pc
# bounds exactly where the dynamic construction stops.
set -u
cd /home/z/my-project
OUT=run/s138_dooz_pmc
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lpm;|c,Ljr1;|<init>,Lj6;|<init>"
export MINIANDROID_THROW_TRACE=1
timeout 590 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 540 \
  --tap 765,1830@12 \
  --dump-view-tree -o "$OUT" 2>"$OUT/pmc.log"
echo "exit=$?"
echo "pmc_lines=$(wc -l < "$OUT/pmc.log")"
echo "pmc_enters=$(rg -c 'PMC. ENTER' "$OUT/pmc.log" 2>/dev/null || echo 0)"
rg -n 'PMC. ENTER' "$OUT/pmc.log" 2>/dev/null | sed -n 1,12p
echo "== last pmc lines =="
rg -n 'PMC' "$OUT/pmc.log" 2>/dev/null | tail -6
