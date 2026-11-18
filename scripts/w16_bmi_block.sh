#!/bin/bash
cd /home/z/my-project/miniandroid
BMI=$(ls /home/z/my-project/upload/handoff_apks/ | grep -iE "bmi" | head -1)
BLK=$(ls /home/z/my-project/upload/handoff_apks/ | grep -iE "blockinger" | head -1)
mkdir -p /tmp/w16/targets
for T in "$BMI" "$BLK"; do
  N=$(echo $T | cut -d_ -f1 | cut -d. -f1-2)
  ./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace -o /tmp/w16/targets/$N --execution-mode real-dalvik /home/z/my-project/upload/handoff_apks/$T > /tmp/w16/targets/$N.log 2>&1
  S=$(sha256sum /tmp/w16/targets/$N/screenshot.png 2>/dev/null | cut -c1-16)
  echo "$N sha=$S exc=$(grep -ac 'APP BOUND\|CRASH' /tmp/w16/targets/$N.log) uncaught=$(grep -ac 'uncaught' /tmp/w16/targets/$N.log)"
done
