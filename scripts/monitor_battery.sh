#!/usr/bin/env bash
# Signal/kill forensic monitor — wraps run_test_battery.sh, logs:
#  * any signal delivered to THIS monitor (TERM/HUP/INT/QUIT)
#  * battery process state every 2s (state, RSS, child pids)
#  * unexpected battery exit time + last log line
LOG=/tmp/monitor.log
BLOG=/tmp/battery_final_s12.log
: > "$LOG"
for s in TERM HUP INT QUIT; do
    trap "echo \"$(date +%T) monitor got SIG$s\" >> $LOG; exit 99" $s
done
echo "$(date +%T) monitor start pid=$$" >> "$LOG"
setsid bash /home/z/my-project/MiniAndroid-Compatibility-Runtime/scripts/run_test_battery.sh \
    > "$BLOG" 2>&1 &
BPID=$!
echo "$(date +%T) battery pid=$BPID" >> "$LOG"
while kill -0 "$BPID" 2>/dev/null; do
    ST=$(ps -o stat= -p "$BPID" 2>/dev/null | tr -d ' ')
    RSS=$(ps -o rss= -p "$BPID" 2>/dev/null | tr -d ' ')
    CH=$(ps --ppid "$BPID" -o pid=,comm= 2>/dev/null | tr '\n' ';')
    echo "$(date +%T) battery state=$ST rss=$RSS children=[$CH]" >> "$LOG"
    sleep 2
done
echo "$(date +%T) battery EXITED monitor_alive=yes" >> "$LOG"
tail -3 "$BLOG" >> "$LOG" 2>/dev/null
