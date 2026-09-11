#!/usr/bin/env bash
# monitor_m9_dooz.sh — launch dooz under a 2s-interval forensic monitor
# (M3-S12 worklog law: kills are external/harness-level, not OOM; the
# monitor captures RSS/state every 2s so the kill point is evidenced).
set -u
cd /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid
OUT=run/m9_dooz_m9a
rm -rf "$OUT"
MON=/tmp/m9_dooz_monitor.csv
echo "t_sec,rss_kb,state" > "$MON"
export MINIANDROID_DISPATCH_ATTACH=1
setsid nohup ./build/miniandroid run --execution-mode real-dalvik -o "$OUT" \
  download/exp076_corpus/io.github.yamin8000.dooz_18.apk \
  > /tmp/m9_dooz_run.log 2>&1 < /dev/null &
PID=$!
echo "PID=$PID" >> "$MON"
START=$(date +%s)
while kill -0 "$PID" 2>/dev/null; do
  T=$(( $(date +%s) - START ))
  RSS=$(awk '/VmRSS/{print $2}' "/proc/$PID/status" 2>/dev/null)
  ST=$(awk '/^State/{print $2}' "/proc/$PID/status" 2>/dev/null)
  echo "$T,${RSS:-DEAD},${ST:-X}" >> "$MON"
  sleep 2
done
echo "done rc=?" >> "$MON"
wait "$PID"; RC=$?
echo "EXIT_RC=$RC" >> "$MON"
echo "monitor complete rc=$RC"
