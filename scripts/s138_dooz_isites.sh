#!/usr/bin/env bash
# S138 dooz train (next station after the PMC refutation):
# car-9's "Ljr1; never constructed" is REFUTED at HEAD (7 ctor runs live,
# Lj6;.<init> once) — but zero handler activity post-tap. Decode the FULL
# R8 call graph of the pointerInput element (Ljr1;) with the S136c
# INVOKE-SITES entry dump during touch dispatch: which methods SHOULD run
# when a pointer event arrives, so the next watchlist is exact.
set -u
cd /home/z/my-project
OUT=run/s138_dooz_isites
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_INVOKE_SITES="Ljr1;|"
export MINIANDROID_THROW_TRACE=1
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 520 \
  --tap 765,1830@5 \
  --dump-view-tree -o "$OUT" 2>"$OUT/isites.log"
echo "exit=$?"
echo "== invoke-site dump (Ljr1; methods) =="
rg -n 'INVOKE-SITE' "$OUT/isites.log" 2>/dev/null | sed -n 1,60p
echo "total_sites=$(rg -c 'INVOKE-SITE' "$OUT/isites.log" 2>/dev/null || echo 0)"
