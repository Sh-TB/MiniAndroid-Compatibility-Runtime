#!/usr/bin/env python3
"""CAMPAIGN 010 R1 — extract PNG corpus from real APKs + profile IHDR (bit depth/color/interlace)."""
import zipfile, struct, os, json, collections

APKS = {
    "gmdice": "/home/z/my-project/repo/miniandroid/download/corpus/gmdice.apk",
    "dooz": "/home/z/my-project/repo/miniandroid/download/corpus/dooz.apk",
    "simplestopwatch": "/home/z/my-project/repo/miniandroid/download/corpus/simplestopwatch.apk",
    "telegram": "/home/z/my-project/repo/miniandroid/download/exp038_telegram/Telegram.apk",
    "auxio": os.path.expanduser("~/.cache/miniandroid/apks/org.oxycblt.auxio_75.apk"),
    "newpipe": os.path.expanduser("~/.cache/miniandroid/apks/org.schabi.newpipe_1015.apk"),
    "mindustry": os.path.expanduser("~/.cache/miniandroid/apks/io.anuke.mindustry_1107.apk"),
    "spd": os.path.expanduser("~/.cache/miniandroid/apks/com.shatteredpixel.shatteredpixeldungeon_896.apk"),
}
OUT = "/home/z/my-project/repo/miniandroid/run/uc010_png_corpus"
os.makedirs(OUT, exist_ok=True)

CT = {0: "gray", 2: "rgb", 3: "palette", 4: "gray+alpha", 6: "rgba"}
prof = collections.Counter()
manifest = []
sig = b"\x89PNG\r\n\x1a\n"
for tag, apk in APKS.items():
    if not os.path.exists(apk):
        print(f"SKIP missing {tag}"); continue
    n = 0
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if name.lower().endswith(".png"):
                try:
                    data = z.read(name)
                except Exception:
                    continue
                if not data.startswith(sig) or len(data) < 33:
                    continue
                w, h = struct.unpack(">II", data[16:24])
                bd, ct, interlace = data[24], data[25], data[28]
                prof[(bd, CT.get(ct, ct), interlace)] += 1
                safe = f"{tag}_{n:04d}_{os.path.basename(name).replace('/','_')}"
                with open(os.path.join(OUT, safe), "wb") as f:
                    f.write(data)
                manifest.append({"apk": tag, "entry": name, "file": safe,
                                 "w": w, "h": h, "bit_depth": bd,
                                 "color_type": CT.get(ct, str(ct)), "interlace": interlace,
                                 "bytes": len(data)})
                n += 1
with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print(f"extracted {len(manifest)} PNGs -> {OUT}")
print("profile (bit_depth, color_type, interlace): count")
for k, v in sorted(prof.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
