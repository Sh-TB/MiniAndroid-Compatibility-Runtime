#!/usr/bin/env bash
# T0 baseline — 5 approved targets x 3 runs at exact HEAD, W21 runner shape.
# APK sources recorded in the T0 evidence pack (F-Droid pinned / handoff).
set -u
cd /home/z/my-project/miniandroid
CACHE=/home/z/my-project/apk_cache
OUT=evidence/t0
mkdir -p "$OUT"

declare -A APKS=(
  [dooz]="io.github.yamin8000.dooz_18.apk"
  [rttt]="org.kirkezz.rttt_3.apk"
  [freebloks]="de.saschahlusiak.freebloks_186.apk"
  [dicer]="org.secuso.privacyfriendlydicer_101.apk"
  [itsfrz]="com.itsfrz.tictactoe_5.apk"
)

SUMMARY="$OUT/t0_baseline.tsv"
echo -e "apk\trep\tfirst\tlast\twall_s\trc\tstderr_frames\tsnapshot_sha" > "$SUMMARY"

for name in dooz rttt freebloks dicer itsfrz; do
  apk="$CACHE/${APKS[$name]}"
  for rep in 1 2 3; do
    d="$OUT/${name}_r${rep}"
    rm -rf "$d"; mkdir -p "$d"
    t0=$(date +%s.%N)
    timeout 90 ./build/miniandroid run \
      --max-seconds 60 --frames 30 \
      --data-root "$OUT/${name}_data" \
      -o "$d" \
      --execution-mode real-dalvik \
      "$apk" > "$d/stdout.log" 2> "$d/stderr.log"
    rc=$?
    t1=$(date +%s.%N)
    wall=$(echo "$t1 - $t0" | bc)
    frames=$(grep -cE "frame|Frame" "$d/stderr.log" 2>/dev/null || echo 0)
    snap=$(ls -t "$d"/*.png "$d"/frames/*.png 2>/dev/null | head -1)
    sha=$([ -n "$snap" ] && sha256sum "$snap" | cut -c1-16 || echo none)
    echo -e "$name\t$rep\t$t0\t$t1\t$wall\t$rc\t$frames\t$sha" >> "$SUMMARY"
    echo "[$name r$rep] rc=$rc wall=${wall}s snap_sha=$sha"
  done
done
echo "SUMMARY -> $SUMMARY"
