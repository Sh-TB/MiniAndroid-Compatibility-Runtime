#!/usr/bin/env python3
"""CONT-21 / Issue #384 — Phase C: shared-primitive clustering scan.

Scans every family run.log for the candidate shared primitives and emits
run/cont21/cluster_scan.json with exact per-target evidence lines.
"""
import json, os, re

OUTROOT = "/home/z/my-project/run/cont21/family"

PATTERNS = {
    "P1_providerinfo_metadata": r"ProviderInfo;.metaData|ApplicationInfo;.metaData",
    "P2_uncaught_handler_null": r"Thread\$UncaughtExceptionHandler",
    "P3_kotlin_reflect_forname": r"ReflectionFactoryImpl",
    "P4_arr_len_null": r"ARR-LEN-NULL",
    "P5_native_unsatisfied": r"UnsatisfiedLinkError",
    "P6_surfaceholder": r"SurfaceHolder",
    "P7_uri_null": r"Landroid/net/Uri;\.toString.{0,60}null",
    "P8_stream_path_dup": r"runtime/data/data/data",
    "P9_appinitializer": r"AppInitializer",
    "P10_gdx_surface": r"badlogic/gdx",
}

scan = {}
for t in sorted(os.listdir(OUTROOT)):
    logp = f"{OUTROOT}/{t}/run.log"
    if not os.path.exists(logp):
        continue
    log = open(logp, errors="replace").read()
    row = {}
    for k, pat in PATTERNS.items():
        ms = re.findall(pat, log)
        row[k] = {"count": len(ms), "first": ms[0][:120] if ms else None}
    scan[t] = row

json.dump(scan, open("/home/z/my-project/run/cont21/cluster_scan.json", "w"), indent=1)

# matrix print
keys = list(PATTERNS)
print(f"{'target':14s} " + " ".join(f"{k[1:4]:>4s}" for k in keys))
for t, row in scan.items():
    print(f"{t:14s} " + " ".join(f"{row[k]['count']:>4d}" for k in keys))
print()
print("Legend:", ", ".join(f"{k[1:4]}={k[1:]}" for k in keys))
