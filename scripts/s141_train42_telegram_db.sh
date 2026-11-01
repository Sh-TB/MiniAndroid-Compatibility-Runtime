#!/usr/bin/env bash
# s141_train42_telegram_db.sh — TRAIN-42: where do the SQLiteException x41
# come from? Full-frame run with throw traces + API-call status; the goal is
# the exact chain (which open/quer path raises) so the fix (TRAIN-43 car) is
# generic: wire the REAL sqlite shadow into whatever context class telegram
# uses, or fix the specific miss — no app knowledge.
set -u
cd /home/z/my-project
OUT=run/s141/tg_db
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_THROW_TRACE=1
timeout 420 ./miniandroid/build/miniandroid run upload/telegram_official.apk \
  --width 1080 --height 1920 --frames 40 --max-seconds 380 -o "$OUT" \
  > "$OUT/run.log" 2>"$OUT/err.log"
echo "exit=$?"
echo "== exception census =="
rg -c "SQLiteException" "$OUT/err.log" 2>/dev/null || echo 0
echo "== first 8 SQLite throws with chain =="
rg -n "SQLiteException|THROW|GATEA-DBOPEN|SQLITE-SHADOW" "$OUT/err.log" 2>/dev/null | head -24
echo "== sqlite shadow lines =="
rg -c "SQLITE-SHADOW" "$OUT/err.log" 2>/dev/null || echo 0
echo "== face =="
if [ -f "$OUT/screenshot.png" ]; then sha256sum "$OUT/screenshot.png" | cut -c1-16; else echo NO_SHOT; fi
