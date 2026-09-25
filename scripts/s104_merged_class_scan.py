#!/usr/bin/env python3
"""S104: scan the full corpus APKs for the R8 horizontal-class-merging
signature: a field literally named `$r8$classId` (byte) in classes*.dex.
The S103 u001_typescan.json APK list = the census universe."""
import glob, json, os, zipfile

OUT = "run/s104/merged_class_scan.json"

apks = sorted(glob.glob("/home/z/my-project/run/s99/apks/*.apk"))
rows = []
for apk in apks:
    sig = False
    classes_with = []
    try:
        zf = zipfile.ZipFile(apk)
        for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
            data = zf.read(name)
            # cheap needle scan: $r8$classId appears in the string pool iff any
            # merged class exists in this dex (deterministic: exact ULEB string)
            needle = b"$r8$classId"
            pos = data.find(needle)
            if pos >= 0:
                sig = True
                classes_with.append(name)
    except Exception as e:
        rows.append({"apk": os.path.basename(apk), "error": str(e)})
        continue
    rows.append({"apk": os.path.basename(apk), "r8_merged": sig, "dexes": classes_with})

merged = [r for r in rows if r.get("r8_merged")]
os.makedirs("run/s104", exist_ok=True)
with open(OUT, "w") as f:
    json.dump({"total_apks": len(rows), "r8_merged_apks": len(merged), "rows": rows}, f, indent=1)
print(f"total={len(rows)} r8_merged={len(merged)}")
for r in merged:
    print("  MERGED:", r["apk"])
