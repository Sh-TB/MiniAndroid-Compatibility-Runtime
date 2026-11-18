#!/usr/bin/env python3
"""FINAL Phase 4: identity of the 3 candidate APKs (sha256, size, package/version)."""
import hashlib, zipfile, re, os, json
CANDS = ["com.farmerbb.notepad_122.apk", "name.livitski.games.puzzle.android_2.apk",
         "org.blockinger.game_14.apk"]
out = {}
for a in CANDS:
    p = f"/home/z/my-project/upload/handoff_apks/{a}"
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    z = zipfile.ZipFile(p)
    mf = z.read("AndroidManifest.xml")
    s16 = mf.decode("utf-16-le", errors="ignore")
    strs = re.findall(r"[\x20-\x7e]{4,}", s16)
    pkg = next((s for s in strs if re.match(r"^[a-z][a-z0-9_.]+$", s) and s.count(".") >= 2), "?")
    ver = [s for s in strs if re.match(r"^\d+(\.\d+){1,3}[\w.-]*$", s)][:4]
    sizes = sorted(z.infolist(), key=lambda i: -i.file_size)[:3]
    out[a] = {"sha256": h, "size_mb": round(os.path.getsize(p)/1048576, 2),
              "package_guess": pkg, "versionish_strings": ver,
              "dex_files": [n for n in z.namelist() if n.endswith(".dex")],
              "largest_entries": [(i.filename.split("/")[-1], i.file_size//1024) for i in sizes],
              "native_libs": [n for n in z.namelist() if "/lib/" in n][:3]}
    print(a, json.dumps(out[a], indent=1))
json.dump(out, open("/tmp/f_apk_idents.json", "w"), indent=1)
