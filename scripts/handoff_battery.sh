#!/bin/bash
# Wave A: run the 6 handoff-target APKs through the runtime, bounded.
cd /home/z/my-project/miniandroid
OUT=/tmp/handoff_evidence
mkdir -p $OUT
: > $OUT/progress.txt
for apk in /home/z/my-project/upload/handoff_apks/*.apk; do
    name=$(basename "$apk" .apk)
    d=$OUT/$name
    start=$(date +%s)
    timeout 180 ./build/miniandroid run "$apk" -o "$d" --max-seconds 90 > "$OUT/$name.log" 2>&1
    rc=$?
    wall=$(( $(date +%s) - start ))
    status=$(grep -oE "Status: (SUCCESS|PARTIAL|FAILED)[^ ]*" "$OUT/$name.log" | head -1 | sed 's/Status: //')
    frames=$(grep -oE "Frames Rendered: [0-9]+" "$OUT/$name.log" | grep -oE "[0-9]+")
    errors=$(grep -oE "Errors: [0-9]+" "$OUT/$name.log" | head -1 | grep -oE "[0-9]+")
    nw="no-shot"
    [ -f "$d/screenshot.png" ] && nw=$(python3 -c "from PIL import Image; im=Image.open('$d/screenshot.png').convert('L'); h=im.histogram(); print(round(1-h[255]/sum(h),3))" 2>/dev/null)
    crash=$(grep -cE "SIGSEGV|FATAL|Forensics" "$OUT/$name.log")
    echo "$name | rc=$rc | ${wall}s | $status | frames=$frames | errors=$errors | nonwhite=$nw | crashhits=$crash" >> $OUT/summary.txt
    echo "done: $name rc=$rc $status" >> $OUT/progress.txt
done
echo "WAVE-A COMPLETE" >> $OUT/summary.txt
