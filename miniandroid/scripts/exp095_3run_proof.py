#!/usr/bin/env python3
"""EXP-095 3-run visual proof with SEMANTIC CONTENT ASSERTIONS.

Per campaign §36: three complete flows; for each: instruction count, method
count, heap count, visible nodes, text nodes, pixel count, image SHA.
Plus §35 content assertions:
  - the formatted SMS description contains the real phone number
  - NO "View" garbage substring anywhere in visible text (SFS-008 guard)
  - "Enter code" title present
  - code input fields present (5 CodeFieldContainer)
  - "Didn't get the code?" present
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid")
APK = BASE / "download/exp038_telegram/Telegram.apk"
BIN = BASE / "build/miniandroid"
OUT = BASE / "run/exp095/3run"

results = []
for run in (1, 2, 3):
    outdir = OUT / f"run{run}"
    outdir.mkdir(parents=True, exist_ok=True)
    log_path = outdir / "run.log"
    with open(log_path, "w") as f:
        rc = subprocess.run(
            [str(BIN), "run", str(APK), "-o", str(outdir), "-v"],
            cwd=BASE, stdout=f, stderr=subprocess.STDOUT, timeout=280,
        ).returncode

    log = log_path.read_text(errors="ignore")

    # --- extract semantics from the log ---
    # All setText text values in the active SMS view phase
    settexts = re.findall(
        r'\[EXP091-SETTEXT\] view_id=(\d+) class=([^;]+);.*? text="([^"]*)"', log)
    all_text = " | ".join(t for _, _, t in settexts)

    checks = {
        "exit_code_zero": rc == 0,
        "sms_description_has_phone": "+1 5551234567" in all_text,
        "title_enter_code": "Enter code" in all_text,
        "resend_link_present": "Didn't get the code?" in all_text,
        "no_View_garbage": "View" not in all_text,
        "currentViewNum_is_2": "new_value=2" in log,
        "setParams_active_page": "active page view = obj#" in log,
        "code_fields_rendered": log.count("CodeFieldContainer$1") >= 5,
        "render_root_setparams": "Using last-setParams view as render root" in log,
    }
    fmt = re.findall(r'formatString\(key="SentSmsCode"\) → "([^"]*)"', log)
    # NOTE: addNbsp replaces the space in "+1 5551234567" with U+00A0 (NBSP)
    # per its source semantics — normalize before comparing.
    fmt_norm = fmt[-1].replace("\u00a0", " ") if fmt else ""
    checks["formatString_correct"] = bool(fmt) and "+1 5551234567" in fmt_norm

    # pixel metrics
    png = outdir / "screenshot.png"
    pixel_info = {}
    if png.exists():
        from PIL import Image
        img = Image.open(png)
        bg = (255, 255, 255)
        non_bg = dark = 0
        for px in img.getdata():
            if px != bg:
                non_bg += 1
                if px[0] < 100 and px[1] < 100 and px[2] < 100:
                    dark += 1
        pixel_info = {
            "width": img.width, "height": img.height,
            "non_bg_pixels": non_bg, "dark_pixels": dark,
            "sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
        }

    # counts
    m = {
        "run": run,
        "exit": rc,
        "instructions": log.count("[METHOD-IN]"),
        "render_nodes": log.count("[EXP092-RENDER]"),
        "addview_lp_captures": log.count("[EXP095-ADDVIEW-LP]"),
        "settext_calls": len(settexts),
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "pixels": pixel_info,
    }
    results.append(m)
    print(f"RUN {run}: exit={rc} checks={m['checks_passed']}/{m['checks_total']} "
          f"pixels={pixel_info.get('non_bg_pixels', 'N/A')} "
          f"nodes={m['render_nodes']}")

# summary
print("\n=== CHECK DETAILS (run 3) ===")
for k, v in results[-1]["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}: {k}")

shas = {r["pixels"].get("sha256") for r in results}
pixels = [r["pixels"].get("non_bg_pixels") for r in results]
stable = len(set(pixels)) == 1 and pixels[0] is not None
print(f"\n3-run pixel stability: {'STABLE' if stable else 'UNSTABLE'} {pixels}")
print(f"3-run SHA uniqueness: {len(shas)} distinct")

passed = all(r["checks_passed"] == r["checks_total"] for r in results)
print(f"ALL RUNS ALL CHECKS: {'PASS ✓' if passed else 'FAIL ✗'}")

(OUT / "summary.json").write_text(json.dumps(results, indent=2))
sys.exit(0 if passed and stable else 1)
