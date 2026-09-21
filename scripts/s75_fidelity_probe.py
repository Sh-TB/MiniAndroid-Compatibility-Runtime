#!/usr/bin/env python3
"""s75_fidelity_probe.py — S75 Level C regression probe.

Recipe (S56/S73 replay law): replay the EXACT autonomous 23-tap schedule
(recovered from the committed run_01 gameplay_trace.json 'input' fields) as
a fresh run on the current binary, then compare every per-frame PNG SHA256
against the stored run_01 frames. Byte-identical 90/90 proves the A7 runtime
change did not perturb the observed render pipeline (A7 touches manifest
label resolution only; the replay is the strongest evidence for that claim).
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s72_w4_apks/snake_v1.0_vc1.apk"
SRC = f"{ROOT}/docs/evidence/s73_snake_autoplay/run_01"
OUT = f"{ROOT}/docs/evidence/s75/snake_fidelity_probe"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    taps = []
    for line in open(f"{SRC}/gameplay_trace.json", encoding="utf-8",
                     errors="replace"):
        m = re.search(r"tap\((\d+),(\d+)\)@frame(\d+)", line)
        if m:
            taps.append(f"{m.group(1)},{m.group(2)}@{m.group(3)}")
    assert len(taps) == 23, f"expected 23 taps, got {len(taps)}"

    stored = sorted(glob.glob(f"{SRC}/frames/frame_*.png"))
    n_frames = len(stored)
    print(f"schedule: {len(taps)} scheduled taps, {n_frames} stored frames")

    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(f"{OUT}/frames/frame_*.png"):
        os.remove(f)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", "250",
           "--dump-view-tree", "-o", OUT]
    for t in taps:
        cmd += ["--tap", t]
    cmd += [APK]
    with open(f"{OUT}/engine.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)

    fresh = sorted(glob.glob(f"{OUT}/frames/frame_*.png"))
    print(f"fresh rc={rc} frames={len(fresh)}")

    n_cmp = min(len(stored), len(fresh))
    match = sum(1 for a, b in zip(stored, fresh) if sha256(a) == sha256(b))
    mismatches = [(os.path.basename(a), os.path.basename(b))
                  for a, b in zip(stored, fresh) if sha256(a) != sha256(b)][:10]
    verdict = ("BYTE-IDENTICAL 90/90"
               if n_cmp == 90 and match == 90 and len(fresh) == 90
               else f"PARTIAL {match}/{n_cmp} (fresh frames {len(fresh)})")
    report = {
        "probe": "S75 Level C snake fidelity (replay of committed 23-tap schedule)",
        "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()[:8],
        "rc": rc, "stored_frames": len(stored), "fresh_frames": len(fresh),
        "matching_frames": match, "compared": n_cmp,
        "mismatch_samples": mismatches, "verdict": verdict,
    }
    with open(f"{OUT}/fidelity_report.json", "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if "BYTE-IDENTICAL" in verdict else 1


if __name__ == "__main__":
    sys.exit(main())
