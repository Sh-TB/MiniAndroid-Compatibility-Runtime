#!/usr/bin/env python3
"""ISSUE-612 Phase 1: per-TU compile cost measurement (wall + peak RSS via rusage)."""
import subprocess, resource, time, os, sys, json

os.chdir("/home/z/my-project/miniandroid")
os.makedirs("evidence/issue612_audit", exist_ok=True)
FLAGS = ["-std=c++17", "-Wall", "-Wextra", "-DMINIANDROID_HAVE_WEBP", "-DMINIANDROID_HAVE_LOTTIE",
         "-Isrc", "-Isrc/webview", "-Isrc/apk", "-Isrc/dex", "-Isrc/runtime", "-Isrc/api",
         "-Isrc/graphics", "-Isrc/diagnostics", "-Isrc/resources", "-Isrc/renderer",
         "-Isrc/framework", "-Isrc/storage", "-Isrc/fonts", "-Isrc/gles", "-Isrc/jni",
         "-Isrc/audio", "-Ithird_party/portablegl", "-I/usr/include/freetype2",
         "-Ithird_party/nlohmann_json/include"]
PROFILE = sys.argv[1] if len(sys.argv) > 1 else "-O0 -g0"          # pass A default
PROFILE_FLAGS = PROFILE.split()
ONLY = sys.argv[2:] if len(sys.argv) > 2 else None                  # restrict TUs
rows = []
for root, dirs, files in os.walk("src"):
    for f in sorted(files):
        if not f.endswith(".cpp"):
            continue
        cpp = os.path.join(root, f)
        if ONLY and not any(o in cpp for o in ONLY):
            continue
        stem = cpp[4:].replace("/", "_")[:-4]
        obj = f"build/audit_{PROFILE_FLAGS[0][2:] if PROFILE_FLAGS[0].startswith('-O') else 'O0'}/{stem}.o"
        os.makedirs(os.path.dirname(obj), exist_ok=True)
        before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        t0 = time.monotonic()
        r = subprocess.run(["g++"] + FLAGS + PROFILE_FLAGS + ["-MMD", "-MP", "-c", cpp, "-o", obj],
                           capture_output=True)
        dt = time.monotonic() - t0
        peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss  # KB, cumulative max
        rows.append({"tu": cpp[4:], "sec": round(dt, 2), "rc": r.returncode,
                     "peakMB_new": max(0, peak - before) // 1024, "peakMB_cum": peak // 1024})
        print(f"{cpp[4:]:48s} {dt:7.2f}s rc={r.returncode} peakCum={peak//1024}MB")
rows.sort(key=lambda r: -r["sec"])
tag = PROFILE.replace(" ", "").replace("-", "")
with open(f"evidence/issue612_audit/tu_cost_{tag}.json", "w") as fh:
    json.dump({"profile": PROFILE, "rows": rows}, fh, indent=1)
print("\nTOP 10 by wall time:")
for r in rows[:10]:
    print(f"  {r['tu']:44s} {r['sec']}s")
