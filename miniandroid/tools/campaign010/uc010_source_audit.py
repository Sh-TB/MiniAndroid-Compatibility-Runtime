#!/usr/bin/env python3
"""CAMPAIGN 010 §2 — custom implementation audit: LoC census per subsystem + markers (R32 prep)."""
import os, re, json, subprocess, collections

ROOT = "/home/z/my-project/repo/miniandroid/src"
OUT = "/home/z/my-project/repo/miniandroid/database/uc010_source_audit.json"

SUBSYS = {
    "apk/": "APK parser (zip/manifest)",
    "dex/": "DEX parser + interpreter + engine",
    "runtime/": "execution engine / application runtime",
    "resources/": "ARSC/AXML/layout inflater/res-config",
    "renderer/": "software renderer + fonts",
    "graphics/": "graphics helpers",
    "framework/": "Android view shadows / registry",
    "api/": "API dispatcher bridge / context / prefs",
    "storage/": "file sandbox / sqlite / prefs store",
    "diagnostics/": "trace / click audit",
    "jni/": "JNI bridge",
}

census = {}
grand = 0
for d in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p): continue
    files = []
    for f in sorted(os.listdir(p)):
        if f.endswith((".cpp", ".h", ".c", ".cc")):
            fp = os.path.join(p, f)
            with open(fp, "r", errors="ignore") as fh:
                n = sum(1 for _ in fh)
            files.append({"file": f, "loc": n})
    loc = sum(f["loc"] for f in files)
    grand += loc
    census[d] = {"loc": loc, "files": files, "nfiles": len(files),
                 "role": SUBSYS.get(d + "/", "?")}

# root-level mains (exp*_main.cpp etc.)
root_files = []
for f in sorted(os.listdir(ROOT)):
    if f.endswith((".cpp", ".h")):
        fp = os.path.join(ROOT, f)
        with open(fp, errors="ignore") as fh:
            n = sum(1 for _ in fh)
        root_files.append({"file": f, "loc": n})
root_loc = sum(f["loc"] for f in root_files)
grand += root_loc

# R32 marker scan (excluding third_party)
MARK = re.compile(r"\b(TODO|FIXME|HACK|XXX|stub|STUBBED|placeholder|fake|hardcode|silent|no-op)\b")
markers = collections.Counter()
per_file_markers = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ("third_party",)]
    for fn in filenames:
        if not fn.endswith((".cpp", ".h", ".c")): continue
        fp = os.path.join(dirpath, fn)
        rel = os.path.relpath(fp, ROOT)
        cnt = 0
        with open(fp, errors="ignore") as fh:
            for line in fh:
                if MARK.search(line): cnt += 1
        if cnt:
            markers[rel.split("/")[0]] += cnt
            per_file_markers[rel] = cnt

# Linked external libs (from Makefile)
mk = open("/home/z/my-project/repo/miniandroid/Makefile").read()
linked = re.findall(r"-l([a-z0-9_]+)", mk)

result = {
    "campaign": "010",
    "total_src_loc": grand,
    "per_dir": census,
    "root_files_loc": root_loc,
    "root_files": root_files,
    "markers_per_dir": dict(markers),
    "markers_total": sum(markers.values()),
    "markers_top_files": dict(sorted(per_file_markers.items(), key=lambda kv: -kv[1])[:30]),
    "linked_libs": linked,
}
with open(OUT, "w") as fh:
    json.dump(result, fh, indent=1)
print(f"TOTAL src LoC: {grand}")
for d, v in sorted(census.items(), key=lambda kv: -kv[1]["loc"]):
    print(f"  {d:16s} {v['loc']:7,} LoC  {v['nfiles']:3d} files  {v['role']}")
print(f"  {'(root mains)':16s} {root_loc:7,} LoC")
print(f"\nMarker scan (src/ only): {sum(markers.values())} hits -> {dict(markers)}")
print(f"Linked libs: {linked}")
print(f"Saved: {OUT}")
