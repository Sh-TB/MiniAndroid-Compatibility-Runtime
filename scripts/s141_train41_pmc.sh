#!/usr/bin/env bash
# s141_train41_pmc.sh — TRAIN-41 live probe: the factory-lambda DISPATCH law.
# Static law (probes A/B/C): Luq;.h is the ONLY caller of the clickable
# factory body Lpm;.c (invoke-static/range pc=75, 18 regs); Luq; implements
# Function2 (Lj90;) capturing 17 values incl. Lom;; Lq; (super Lgk0;) is the
# materialize folder (Function2, 324 insns, packed-switch, factory arm
# pc=160 -> Lk90;.f Function3). ZERO static callers of both = interface
# dispatch only.
# THIS PROBE answers, live:
#   (1) is the factory lambda CONSTRUCTED?  (Luq;|<init>)
#   (2) does dispatch ever land on it?      (Luq;|h)
#   (3) which branch does the folder take?  (Lq;|h last-pc law)
#   (4) does the Function3 factory interface fire? (Lk90;|f)
set -u
cd /home/z/my-project
OUT=run/s141_train41_pmc
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Luq;|<init>,Luq;|h,Lq;|h,Lpm;|c,Lk90;|f,Lom;|h"
export MINIANDROID_THROW_TRACE=1
timeout 590 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 540 \
  --tap 765,1830@12 \
  --dump-view-tree -o "$OUT" 2>"$OUT/pmc.log"
echo "exit=$?"
echo "pmc_lines=$(wc -l < "$OUT/pmc.log")"
for pat in 'Luq;.<init>' 'Luq;.h' 'Lq;.h' 'Lpm;.c' 'Lk90;.f' 'Lom;.h'; do
  echo "enters[$pat]=$(rg -c "PMC. ENTER.*$pat" "$OUT/pmc.log" 2>/dev/null || echo 0)"
done
echo "== Lq;.h last pcs (branch law) =="
rg 'PMC' "$OUT/pmc.log" | rg 'Lq;.h' | tail -8
echo "== any Luq; lines =="
rg 'Luq;' "$OUT/pmc.log" | head -6
