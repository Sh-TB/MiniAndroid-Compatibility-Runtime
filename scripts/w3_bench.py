#!/usr/bin/env python3
"""W3 benchmark: dalvik_engine.cpp -ftime-report phase breakdown at -O2 and -O0.
Same machine/compiler/flags-as-profile; records wall, peak RSS, obj size."""
import subprocess, resource, time, os, re, json

os.chdir("/home/z/my-project/miniandroid")
os.makedirs("evidence/issue612_audit/wave3", exist_ok=True)
COMMON = ["-std=c++17", "-Wall", "-Wextra", "-MMD", "-MP", "-DMINIANDROID_HAVE_WEBP",
          "-Isrc", "-Isrc/webview", "-Isrc/apk", "-Isrc/dex", "-Isrc/runtime", "-Isrc/api",
          "-Isrc/graphics", "-Isrc/diagnostics", "-Isrc/resources", "-Isrc/renderer",
          "-Isrc/framework", "-Isrc/storage", "-Isrc/fonts", "-Isrc/gles", "-Isrc/jni",
          "-Isrc/audio", "-Ithird_party/portablegl", "-I/usr/include/freetype2",
          "-Ithird_party/nlohmann_json/include"]
results = {}
for tag, opt in (("O2", ["-O2"]), ("O0", ["-O0", "-g0"])):
    obj = f"/tmp/i612_w3_dalvik_{tag}.o"
    rep = f"evidence/issue612_audit/wave3/ftime_report_dalvik_{tag}.txt"
    cmd = ["g++"] + COMMON + opt + ["-ftime-report", "-c", "src/dex/dalvik_engine.cpp", "-o", obj]
    t0 = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    dt = time.monotonic() - t0
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    with open(rep, "w") as f:
        f.write(r.stderr)
    # GCC phase lines: " <phase name>:\n  <time> (...)
    phases = {}
    cur = None
    for line in r.stderr.splitlines():
        m = re.match(r"\s{2}(\S.*):\s*$", line)
        if m and not line.strip().startswith(("(", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            cur = m.group(1).strip()
        m2 = re.match(r"\s+(\d+\.\d+)\s*\(", line)
        if m2 and cur and cur.lower() != "total time":
            phases[cur] = phases.get(cur, 0.0) + float(m2.group(1))
    size = os.path.getsize(obj) if os.path.exists(obj) else 0
    results[tag] = {"wall_s": round(dt, 2), "rc": r.returncode, "obj_bytes": size,
                    "peak_rss_mb": peak // 1024, "top_phases": sorted(phases.items(), key=lambda x: -x[1])[:8]}
    print(f"{tag}: wall={dt:.2f}s rc={r.returncode} obj={size/1e6:.1f}MB peak={peak//1024}MB")
    for k, v in results[tag]["top_phases"]:
        print(f"   {v:8.2f}s  {k}")
with open("evidence/issue612_audit/wave3/benchmarks.json", "w") as f:
    json.dump(results, f, indent=1)
