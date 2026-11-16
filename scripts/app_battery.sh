#!/bin/bash
# E-wave APP-LOAD BATTERY: run every canonical APK through the runtime,
# bounded, and produce a verdict table.
cd /home/z/my-project/miniandroid
OUT=/tmp/appevidence
SUMMARY=$OUT/battery_summary.txt
: > $SUMMARY
for apk in /home/z/my-project/upload/canonical_apks/*.apk; do
    name=$(basename "$apk" .apk)
    d=$OUT/$name
    start=$(date +%s)
    timeout 150 ./build/miniandroid run "$apk" -o "$d" --max-seconds 60 > "$OUT/$name.log" 2>&1
    rc=$?
    end=$(date +%s)
    wall=$((end - start))
    status=$(grep -oE "Status: (SUCCESS|PARTIAL|FAILED)[^ ]*" "$OUT/$name.log" | head -1 | sed 's/Status: //')
    frames=$(grep -oE "Frames Rendered: [0-9]+" "$OUT/$name.log" | grep -oE "[0-9]+")
    errors=$(grep -oE "Errors: [0-9]+" "$OUT/$name.log" | head -1 | grep -oE "[0-9]+")
    shot="no"
    [ -f "$d/screenshot.png" ] && shot=$(python3 -c "from PIL import Image; im=Image.open('$d/screenshot.png').convert('L'); h=im.histogram(); nw=1-h[255]/sum(h); print(f'{nw:.3f}')" 2>/dev/null)
    crash=$(grep -cE "CRASH|SIGSEGV|FATAL|Forensics" "$OUT/$name.log")
    echo "$name | rc=$rc | wall=${wall}s | $status | frames=$frames | errors=$errors | nonwhite=$shot | crashhits=$crash" >> $SUMMARY
    echo "done: $name (rc=$rc $status)" >> $OUT/progress.txt
done
echo "BATTERY COMPLETE" >> $SUMMARY
