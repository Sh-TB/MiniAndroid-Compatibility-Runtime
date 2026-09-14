#!/usr/bin/env python3
"""S41 Attack-5: cross-app regression matrix with the R-NEW-345/346 build.
Runs the key corpus APKs + hello fixtures; records rc/status/screenshot SHA/
nonwhite pixels. Verifies (a) no regression from the S41 generic fixes,
(b) quantifies any improvement."""
import subprocess, hashlib, os, json, sys

RUNNER = '/home/z/my-project/miniandroid/build/miniandroid'
OUT = '/tmp/s41/regress'
os.makedirs(OUT, exist_ok=True)

TARGETS = [
    ("gmdice",        "/tmp/my-project/apk_cache/de.duenndns.gmdice_8.apk",        120),
    ("stopwatch",     "/tmp/my-project/apk_cache/com.github.muellerma.stopwatch_6.apk", 120),
    ("microtimer",    "/tmp/my-project/apk_cache/dubrowgn.microtimer_8.apk",        120),
    ("tictactoe",     "/tmp/my-project/apk_cache/com.emmanuelmess.tictactoe_3.apk", 150),
    ("dooz_18",       "/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk",  150),
    ("bouncy",        "/tmp/my-project/apk_cache/corpus/bouncy.apk",                120),
    ("unote",         "/tmp/my-project/apk_cache/app.varlorg.unote_30.apk",         120),
]

def png_nonwhite(path):
    try:
        from PIL import Image
        img = Image.open(path).convert('RGB')
        w, h = img.size
        px = img.load()
        nw = sum(1 for y in range(0, h, 4) for x in range(0, w, 4)
                 if px[x, y] != (255, 255, 255))
        return nw, len(set(img.getdata()))
    except Exception as e:
        return -1, -1

results = []
for name, apk, budget in TARGETS:
    if not os.path.exists(apk):
        results.append({"name": name, "apk": apk, "status": "MISSING-APK"})
        continue
    outdir = f"{OUT}/{name}"
    os.makedirs(outdir, exist_ok=True)
    cmd = ["timeout", str(budget), RUNNER, "run", apk, "-o", outdir]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        rc = r.returncode
    except Exception as e:
        rc = -99
    shot = f"{outdir}/screenshot.png"
    sha = ""
    nw = cw = -1
    if os.path.exists(shot):
        sha = hashlib.sha256(open(shot, 'rb').read()).hexdigest()[:16]
        nw, cw = png_nonwhite(shot)
    report = f"{outdir}/report.md"
    status = ""
    if os.path.exists(report):
        for line in open(report):
            if line.startswith("- **Status:**"):
                status = line.split(":")[1].strip()
                break
    results.append({"name": name, "rc": rc, "status": status,
                    "sha256_16": sha, "nonwhite_sampled": nw,
                    "colors": cw})
    print(f"{name:12s} rc={rc:3d} {status:22s} nw={nw:7d} colors={cw:6d} {sha}")

json.dump(results, open(f"{OUT}/s41_regress_summary.json", "w"), indent=1)
print("saved", f"{OUT}/s41_regress_summary.json")
