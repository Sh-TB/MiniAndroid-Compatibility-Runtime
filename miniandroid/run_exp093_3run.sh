#!/bin/bash
# EXP-093 3-RUN PROOF with SMS acceptance gate verification
set -e
cd /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid

OUT_BASE=run/exp093/3run
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
import hashlib, json
from PIL import Image
from pathlib import Path

base = Path("run/exp093/3run")
runs = []
for i in [1, 2, 3]:
    out = base / f"run{i}"
    if not out.exists():
        runs.append({"run": i, "status": "MISSING"})
        continue
    log = (out / "run.log").read_text(errors="ignore")
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
    setpage = log.count("[EXP092-SETPAGE] ")
    fillnext = log.count("[EXP092-FILLNEXTCODE]")
    reqdel_phoneview = log.count("PhoneView$$ExternalSyntheticLambda2;")
    current_view_num_writes = log.count("[EXP092-CURRENTVIEWNUM-WRITE]")
    sms_render = log.count("Using SmsView as render root")
    mocked_sms = log.count("mocked TL_auth_sentCode WITH type=Sms")
    auth_sendcode = log.count("TL_auth_sendCode")

    # Extract currentViewNum value
    import re
    cvn_matches = re.findall(r'EXP092-CURRENTVIEWNUM-WRITE.*new_value=(\d+)', log)
    cvn_values = [int(v) for v in cvn_matches]

    # Extract setPage page values
    setpage_matches = re.findall(r'EXP092-SETPAGE.*page_value=(\d+)', log)
    setpage_values = [int(v) for v in setpage_matches]

    runs.append({
        "run": i,
        "status": "OK",
        "screenshot_sha256": sha,
        "screenshot_size": png.stat().st_size,
        "dimensions": img.size,
        "non_bg_pixels": non_bg,
        "dark_pixels": dark,
        "setpage_traces": setpage,
        "setpage_values": setpage_values,
        "fillnextcode_traces": fillnext,
        "reqdelegate_phoneview": reqdel_phoneview,
        "currentviewnum_writes": current_view_num_writes,
        "currentviewnum_values": cvn_values,
        "sms_render_root": sms_render > 0,
        "mocked_sms_response": mocked_sms > 0,
        "auth_sendcode_construction": auth_sendcode > 0,
    })

for r in runs:
    print(json.dumps(r, indent=2))
    print()

shas = [r.get("screenshot_sha256") for r in runs if r["status"] == "OK"]
print(f"unique screenshot SHAs: {len(set(shas))}")
print(f"all 3 runs identical: {len(set(shas)) == 1}")

# Check SMS acceptance gate
for r in runs:
    if r["status"] != "OK":
        continue
    print(f"\nRun {r['run']} SMS acceptance gate:")
    print(f"  [x] currentViewNum=2: {2 in r['currentviewnum_values']}")
    print(f"  [x] setPage(2): {2 in r['setpage_values']}")
    print(f"  [x] fillNextCodeParams: {r['fillnextcode_traces'] > 0}")
    print(f"  [x] PhoneView$Lambda2.run: {r['reqdelegate_phoneview'] > 0}")
    print(f"  [x] mocked type=Sms: {r['mocked_sms_response']}")
    print(f"  [x] SmsView render root: {r['sms_render_root']}")
    print(f"  [x] auth.sendCode constructed: {r['auth_sendcode_construction']}")
    print(f"  [x] dark pixels: {r['dark_pixels']}")
EOF
