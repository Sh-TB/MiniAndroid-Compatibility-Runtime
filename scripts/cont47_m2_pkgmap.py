#!/usr/bin/env python3
"""CONT-47 M2: map every apk_cache file (opaque names) to its real package via
androguard manifest parse, then report which NOT_TESTED registry rows unlock.
Output: run/cont47/apk_cache_pkg_map.json"""
import warnings, logging, json, glob, os, sys
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from androguard.core.bytecodes.apk import APK

out = {}
files = sorted(glob.glob("/home/z/my-project/apk_cache/**/*.apk", recursive=True))
files += sorted(glob.glob("/home/z/my-project/upload/*_apks/*.apk"))
files = sorted(set(files))
for i, f in enumerate(files):
    try:
        a = APK(f)
        pkg = a.get_package()
        out[f] = {"pkg": pkg, "size": os.path.getsize(f)}
    except Exception as e:
        out[f] = {"pkg": None, "err": str(e)[:80], "size": os.path.getsize(f)}
    if (i + 1) % 20 == 0:
        print(f"[scan {i+1}/{len(files)}]", flush=True)

json.dump(out, open("/home/z/my-project/run/cont47/apk_cache_pkg_map.json", "w"), indent=1)
rows = [json.loads(l) for l in open("/home/z/my-project/plugins/apps.jsonl") if l.strip()]
nt = {str(r.get("pkg")): (r.get("i"), r.get("t")) for r in rows
      if str(r.get("load")) == "NOT_TESTED"}
unlocked = {f: v["pkg"] for f, v in out.items() if v.get("pkg") in nt}
print("MAP-DONE files=", len(files), "unlocked-NOT_TESTED=", len(unlocked))
for f, p in sorted(unlocked.items()):
    print("UNLOCK", nt[p], p, os.path.basename(f))
