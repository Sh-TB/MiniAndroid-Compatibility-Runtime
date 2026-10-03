#!/bin/bash
# S117 G8 — deterministic Telegram run protocol (pinned for all waves).
# Usage: scripts/s117_tg_run.sh <official|forkgram> <outdir> [extra args...]
set -u
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
WHICH="${1:?official|forkgram}"
OUT="${2:?outdir}"
shift 2 || true
case "$WHICH" in
  official) APK=$BASE/upload/tg/telegram_official.apk ;;
  forkgram) APK=$BASE/upload/tg/forkgram.apk ;;
  *) echo "bad target: $WHICH" >&2; exit 2 ;;
esac
mkdir -p "$OUT"
# Deterministic protocol: fixed data-root per target, fixed budget, fixed screen.
exec "$BIN" run \
  --data-root "$BASE/tmp/s117_dataroot/$WHICH" \
  --width 1080 --height 1920 \
  --max-seconds 120 \
  -o "$OUT" \
  "$@" "$APK"

