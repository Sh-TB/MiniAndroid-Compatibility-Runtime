#!/usr/bin/env bash
# S138 telegram re-measure at current HEAD — deterministic s117 protocol
# (fixed data-root per target). History baseline: LaunchActivity ~236
# dispatch frames with the canned TL_config (cont47 T5 era).
set -u
cd /home/z/my-project
OUT=run/s138_tg_forkgram
rm -rf "$OUT"; mkdir -p "$OUT"
mkdir -p /home/z/my-project/tmp/s117_dataroot/forkgram
export MINIANDROID_THROW_TRACE=1
timeout 590 ./miniandroid/build/miniandroid run upload/forkgram_709208.apk \
  --data-root /home/z/my-project/tmp/s117_dataroot/forkgram \
  --width 1080 --height 1920 --frames 260 \
  --max-seconds 540 \
  -o "$OUT" 2>"$OUT/tg.log"
echo "exit=$?"
if [ -f "$OUT/screenshot.png" ]; then sha256sum "$OUT/screenshot.png" | cut -c1-16; else echo NO_SCREENSHOT; fi
echo "r570_unknown=$(rg -c 'R-NEW-570. unknown' "$OUT/tg.log" 2>/dev/null || echo 0)"
echo "t5_config=$(rg -c 'T5-CONFIG' "$OUT/tg.log" 2>/dev/null || echo 0)"
echo "== unknown request classes seen =="
rg -o 'req_cls=[^ ]+' "$OUT/tg.log" 2>/dev/null | sort | uniq -c | sort -rn | sed -n 1,12p
