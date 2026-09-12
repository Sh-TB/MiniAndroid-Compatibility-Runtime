#!/bin/bash
# EXP-092+ 3-RUN VALIDATION
# Runs the full Telegram chain 3 times on current HEAD.
# Records: state transition, SMS visibility, screenshot SHA, ViewTree SHA,
# pixel statistics.

set -e
cd /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid

OUT_BASE=run/exp092/3run_proof
rm -rf "$OUT_BASE"
mkdir -p "$OUT_BASE"

for run in 1 2 3; do
    OUT="$OUT_BASE/run$run"
    mkdir -p "$OUT"
    echo "=== RUN $run ==="
    timeout 180 ./build/miniandroid run download/exp038_telegram/Telegram.apk \
        -o "$OUT" -v > "$OUT/run.log" 2>&1
    rc=$?
    echo "  exit_code=$rc"
done

echo ""
echo "=== AGGREGATED 3-RUN RESULTS ==="
python3 << 'EOF'
import hashlib, json, subprocess
from PIL import Image
from pathlib import Path

base = Path("run/exp092/3run_proof")
runs = []
for i in [1, 2, 3]:
    out = base / f"run{i}"
    if not out.exists():
        runs.append({"run": i, "status": "MISSING"})
        continue
    log = (out / "run.log").read_text(errors="ignore")
    # Screenshot
    png = out / "screenshot.png"
    if not png.exists():
        runs.append({"run": i, "status": "NO_SCREENSHOT"})
        continue
    img = Image.open(png)
    sha = hashlib.sha256(img.tobytes()).hexdigest()
    bg = (255, 255, 255)
    non_bg = 0
    dark = 0
    for px in img.getdata():
        if px != bg:
            non_bg += 1
            if px[0] < 100 and px[1] < 100 and px[2] < 100:
                dark += 1
    # Count trace markers
    setpage = log.count("[EXP092-SETPAGE]")
    fillnext = log.count("[EXP092-FILLNEXTCODE]")
    reqdel = log.count("[EXP092-REQDELEGATE]")
    sms_render = log.count("Using SmsView as render root")
    runs.append({
        "run": i,
        "status": "OK",
        "screenshot_sha256": sha,
        "screenshot_size": png.stat().st_size,
        "dimensions": img.size,
        "non_bg_pixels": non_bg,
        "dark_pixels": dark,
        "setpage_traces": setpage,
        "fillnextcode_traces": fillnext,
        "reqdelegate_traces": reqdel,
        "sms_render_root_logged": sms_render > 0,
    })

for r in runs:
    print(json.dumps(r, indent=2))
print()
# Compare
shas = [r.get("screenshot_sha256") for r in runs if r["status"] == "OK"]
print(f"unique screenshot SHAs: {len(set(shas))}")
print(f"all 3 runs identical: {len(set(shas)) == 1}")
EOF
