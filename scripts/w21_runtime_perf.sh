#!/usr/bin/env bash
# W21 runtime-performance baseline (Phase 4) — 15 original APKs x 5 reps.
# Identical workload to the W20-K2 baseline (--max-seconds 35 --frames 30,
# outer timeout 60, cold rep1 + warm reps 2-5 sharing a per-APK data-root)
# for direct median comparability, PLUS the fields W20-K2 could not capture:
# CPU time and peak RSS per run (w21_runner.py getrusage), binary/APK hashes,
# blank-screen classification, first-divergence extraction, host metadata.
# Output: evidence/w21/runtime_baseline.tsv (+ per-run dirs + JSON summary).
set -u
cd /home/z/my-project/miniandroid
BIN=./build/miniandroid
OUT=evidence/w21/runtime_perf
mkdir -p "$OUT"
TSV=evidence/w21/runtime_baseline.tsv
RUNNER=/home/z/my-project/scripts/w21_runner.py
HOST_NPROC=$(nproc)
BIN_SHA=$(sha256sum "$BIN" | cut -c1-16)
GIT_HEAD=$(git rev-parse HEAD | cut -c1-16)
echo -e "apk\tapk_sha16\tbin_sha16\thead\trep\tphase\twall_s\tcpu_s\tmaxrss_kb\tsha16\tblank_ratio\trc\tfirst_divergence" > "$TSV"

for APK in /home/z/my-project/upload/handoff_apks/*.apk; do
  name=$(basename "$APK" .apk)
  APK_SHA=$(sha256sum "$APK" | cut -c1-16)
  DR="$OUT/${name}_data"
  for rep in 1 2 3 4 5; do
    d="$OUT/${name}_r${rep}"
    mkdir -p "$d"
    python3 "$RUNNER" timeout 60 "$BIN" run --max-seconds 35 --frames 30 \
      --data-root "$DR" -o "$d" --execution-mode real-dalvik "$APK" \
      > "$d/runner.json" 2> "$d/run.log"
    rc=$(python3 -c "import json;print(json.load(open('$d/runner.json'))['rc'])" 2>/dev/null || echo "?")
    wall=$(python3 -c "import json;print(json.load(open('$d/runner.json'))['wall_s'])" 2>/dev/null || echo "?")
    cpu=$(python3 -c "import json;r=json.load(open('$d/runner.json'));print(round(r['cpu_user_s']+r['cpu_sys_s'],2))" 2>/dev/null || echo "?")
    rss=$(python3 -c "import json;print(json.load(open('$d/runner.json'))['maxrss_kb'])" 2>/dev/null || echo "?")
    sha=$(sha256sum "$d/screenshot.png" 2>/dev/null | cut -c1-16); [ -z "$sha" ] && sha=none
    blank=$(python3 - "$d/screenshot.png" <<'PYEOF' 2>/dev/null || echo "?"
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("L")
h = im.histogram()
print(round(1 - h[255] / max(1, sum(h)), 4))
PYEOF
)
    phase=cold; [ "$rep" -gt 1 ] && phase=warm
    div=$(grep -oiE "uncaught [A-Za-z$._]+(Exception|Error)|[A-Za-z$._]+(Exception|Error): .{0,60}" "$d/run.log" 2>/dev/null | head -1)
    echo -e "$name\t$APK_SHA\t$BIN_SHA\t$GIT_HEAD\t$rep\t$phase\t$wall\t$cpu\t$rss\t$sha\t$blank\t$rc\t${div:-none}" >> "$TSV"
    echo "$name r$rep wall=${wall}s cpu=$cpu rss=$rss sha=$sha blank=$blank rc=$rc div=${div:-none}"
  done
done
echo "HOST: nproc=$HOST_NPROC bin=$BIN_SHA head=$GIT_HEAD"
echo W21_PERF_BASELINE_DONE
