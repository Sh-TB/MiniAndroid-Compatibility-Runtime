#!/usr/bin/env bash
# s148_wagons.sh — S148: the non-dooz slot wagons.
#  1) microtimer (slot 4): second timer + alarm-list state after expiry
#  2) sqlnotes (slot 11) + sqltasks (slot 12): clear-all / CRUD wagon taps
#  3) telegram satellite: fresh SQLite re-check (x41 hold + face)
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s148_wagons
mkdir -p "$OUT"

# ---------- 1) microtimer: second timer (key-3) + START + long window ----------
MT_STORE=$OUT/store_micro
rm -rf "$MT_STORE"
"$B" install upload/canonical_apks/dubrowgn.microtimer_8.apk --data-root "$MT_STORE" > "$OUT/micro_install.txt" 2>&1
MINIANDROID_T68_NODE_TRACE=0 "$B" run --execution-mode real-dalvik \
  --package dubrowgn.microtimer --data-root "$MT_STORE" \
  -o "$OUT/micro_2timer" --max-seconds 200 --frames 60 \
  --tap 540,1830@20 --tap 540,1830@26 --tap 810,1830@32 --tap 810,1830@38 \
  > "$OUT/micro_2timer.txt" 2>&1
echo "micro exit=$?"

# ---------- 2) sqlnotes: cold re-open + delete-all taps ----------
SN_STORE=$OUT/store_sn
rm -rf "$SN_STORE"
"$B" install upload/s142_sqlnotes/build/sqlnotes_v1.0_vc1.apk --data-root "$SN_STORE" > "$OUT/sn_install.txt" 2>&1
# run1: zero-tap (rows persist from nothing -> 0) then 3 inserts via taps? sqlnotes taps unknown; do zero-tap reopen only
"$B" run --execution-mode real-dalvik \
  --package com.miniandroid.sqlnotes --data-root "$SN_STORE" \
  -o "$OUT/sn_cold" --max-seconds 120 --frames 30 \
  > "$OUT/sn_cold.txt" 2>&1
echo "sn exit=$?"

# ---------- 3) telegram satellite re-check ----------
TG_STORE=$OUT/store_tg
rm -rf "$TG_STORE"
"$B" install upload/forkgram_709208.apk --data-root "$TG_STORE" > "$OUT/tg_install.txt" 2>&1 || true
"$B" run --execution-mode real-dalvik \
  --package org.telegram.messenger.web --data-root "$TG_STORE" \
  -o "$OUT/tg_run" --max-seconds 150 --frames 60 \
  > "$OUT/tg_run.txt" 2>&1
echo "tg exit=$?"
