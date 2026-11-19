#!/usr/bin/env bash
# W20 runtime-performance baseline (P0 mission, Phase 1).
# 15 original APKs x 5 reps (1 cold + 4 warm), bounded workload (35s),
# wall + CPU + peak RSS per run via /usr/bin/time where available,
# determinism sha per run. Output: evidence/w20/runtime_baseline.tsv
set -u
cd /home/z/my-project/miniandroid
BIN=./build/miniandroid
OUT=evidence/w20/runtime_perf
mkdir -p "$OUT"
TSV=evidence/w20/runtime_baseline.tsv
echo -e "apk\trep\tphase\twall_s\tcpu_s\tmaxrss_kb\tsha16\trc" > "$TSV"
TIMEBIN=/usr/bin/time
HAVE_TIME=0; [ -x "$TIMEBIN" ] && HAVE_TIME=1

for APK in /home/z/my-project/upload/handoff_apks/*.apk; do
  name=$(basename "$APK" .apk)
  DR="$OUT/${name}_data"
  for rep in 1 2 3 4 5; do
    d="$OUT/${name}_r${rep}"
    mkdir -p "$d"
    t0=$(date +%s%N)
    if [ "$HAVE_TIME" = 1 ]; then
      timeout 60 "$TIMEBIN" -v "$BIN" run --max-seconds 35 --frames 30 \
        --data-root "$DR" -o "$d" --execution-mode real-dalvik "$APK" \
        > "$d/run.log" 2> "$d/time.log"
    else
      timeout 60 "$BIN" run --max-seconds 35 --frames 30 \
        --data-root "$DR" -o "$d" --execution-mode real-dalvik "$APK" \
        > "$d/run.log" 2>&1 || true
    fi
    rc=$?
    t1=$(date +%s%N)
    wall=$(( (t1 - t0) / 1000000 ))
    wall_s=$(awk -v ms="$wall" 'BEGIN{printf "%.2f", ms/1000}')
    if [ "$HAVE_TIME" = 1 ]; then
      cpu=$(grep -E "User time|System time" "$d/time.log" | awk '{s+=$NF} END{printf "%.2f", s}')
      rss=$(grep "Maximum resident" "$d/time.log" | awk '{print $NF}')
    else
      cpu="na"; rss="na"
    fi
    sha=$(sha256sum "$d/screenshot.png" 2>/dev/null | cut -c1-16)
    [ -z "$sha" ] && sha=none
    phase=cold; [ "$rep" -gt 1 ] && phase=warm
    echo -e "$name\t$rep\t$phase\t$wall_s\t$cpu\t$rss\t$sha\t$rc" >> "$TSV"
    echo "$name r$rep wall=${wall_s}s cpu=$cpu rss=$rss sha=$sha rc=$rc"
  done
done
echo PERF_BASELINE_DONE
