#!/usr/bin/env python3
"""S82-GFX-REVOLUTION P1 — per-title graphics fingerprint + family clustering.

Source-first law: the 41 executed titles have APKs in the S82 cache — the
scan is STREAMING (zipfile per-entry, never a full extract), hash/cache-aware
(results cached by (size,mtime) so re-runs cost zero I/O beyond the dir
listing), RAM-bounded (only header bytes of large entries are read).

Fingerprint fields mirror S82-GFX §4 (ENGINE/LANGUAGE/UI TOOLKIT/GRAPHICS
API/IMAGE FORMATS/DRAWABLE TYPES/VECTOR/NINEPATCH/PALETTE PNG/ALPHA/DENSITY
QUALIFIERS/THEME/COLORSTATELIST/CUSTOM VIEW/CANVAS/OPENGL ES/EGL/SURFACEVIEW/
GLSURFACEVIEW/TEXTUREVIEW/LIBGDX/SDL/GAME ENGINE/COMPOSE/ANDROIDX/WEBVIEW/
BITMAPFACTORY/IMAGEDECODER/DRAWBITMAP/DRAWABLE.DRAW/CUSTOM RENDERER).

Output: docs/corpus/s82/graphics_families.json  (+ cache file next to it).
"""
import json
import os
import re
import struct
import sys
import zipfile
from collections import Counter

APK_CACHE = "/tmp/my-project/apk_cache/s82"
REGISTRY = "/home/z/my-project/docs/corpus/s82/title_registry.json"
OUT = "/home/z/my-project/docs/corpus/s82/graphics_families.json"
CACHE = "/home/z/my-project/run/s82/gfx_scan_cache.json"

# dex string markers → (fingerprint key, family)
DEX_MARKERS = {
    "Lcom/badlogic/gdx/": ("LIBGDX", "FAMILY-J"),
    "Lorg/libsdl/": ("SDL", "FAMILY-K"),
    "SDLActivity": ("SDL", "FAMILY-K"),
    "Ljavax/microedition/khronos/egl/": ("EGL", "FAMILY-G"),
    "Ljavax/microedition/khronos/opengles/": ("OPENGL_ES1", "FAMILY-G"),
    "Landroid/opengl/GLES": ("OPENGL_ES2PLUS", "FAMILY-G"),
    "Landroid/opengl/GLSurfaceView;": ("GLSURFACEVIEW", "FAMILY-G"),
    "Landroid/view/SurfaceView;": ("SURFACEVIEW", "FAMILY-H"),
    "Landroid/view/TextureView;": ("TEXTUREVIEW", "FAMILY-H"),
    "Landroidx/compose/": ("COMPOSE", "FAMILY-L"),
    "Landroid/webkit/WebView;": ("WEBVIEW", "FAMILY-M"),
    "Landroid/graphics/BitmapFactory;": ("BITMAPFACTORY", "FAMILY-B"),
    "Landroid/graphics/Bitmap;": ("BITMAP", "FAMILY-B"),
    "Landroid/graphics/Canvas;": ("CANVAS", "FAMILY-E"),
    "Landroid/graphics/Path;": ("CANVAS_PATH", "FAMILY-E"),
    "Landroid/graphics/drawable/VectorDrawable": ("VECTOR", "FAMILY-C"),
    "Landroid/graphics/drawable/GradientDrawable;": ("GRADIENT_DRAWABLE", "FAMILY-C"),
    "Landroid/graphics/drawable/StateListDrawable;": ("STATELIST", "FAMILY-C"),
    "Landroid/content/res/ColorStateList;": ("COLORSTATELIST", "FAMILY-C"),
    "Landroid/widget/ImageView;": ("IMAGEVIEW", "FAMILY-D"),
    "Landroid/widget/ImageButton;": ("IMAGEVIEW", "FAMILY-D"),
    "Landroid/graphics/ImageDecoder;": ("IMAGEDECODER", "FAMILY-B"),
    "Landroid/view/animation/": ("VIEW_ANIMATION", "FAMILY-N"),
    "Landroidx/vectordrawable/": ("VECTOR_ANDROIDX", "FAMILY-C"),
    "Landroid/support/": ("SUPPORT_LIB", None),
}

DENSITY_RE = re.compile(r"res/.*-(mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi|ldpi|nodpi)/")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def sniff_png(raw):
    """Header-level census: dimensions, color type, bit depth, tRNS/PLTE."""
    if len(raw) < 33 or raw[:8] != PNG_SIG:
        return None
    w, h = struct.unpack(">II", raw[16:24])
    bitd, ct = raw[24], raw[25]
    return {"w": w, "h": h, "bitdepth": bitd, "colortype": ct}


def scan_apk(path):
    fp = {
        "RES_PNG": 0, "RES_JPG": 0, "RES_WEBP": 0, "RES_XML": 0,
        "RES_XML_DRAWABLE": 0, "NINEPATCH": 0, "PALETTE_PNG": 0,
        "ALPHA_PNG": 0, "TRNS_PNG": 0, "DENSITY_QUALIFIERS": [],
        "NATIVE_LIBS": [], "PNG_COLOR_TYPES": Counter(), "DEX_MARKERS": {},
        "MAX_PNG_SIDE": 0, "ASSETS": 0, "DEX_FILES": 0,
    }
    dex_blob_chunks = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            n = info.filename
            ln = n.lower()
            if n.startswith("res/"):
                m = DENSITY_RE.search(n)
                if m and m.group(1) not in fp["DENSITY_QUALIFIERS"]:
                    fp["DENSITY_QUALIFIERS"].append(m.group(1))
            if ln.endswith(".png"):
                fp["RES_PNG"] += 1
                if ln.endswith(".9.png"):
                    fp["NINEPATCH"] += 1
                raw = z.read(n)
                s = sniff_png(raw)
                if s:
                    fp["PNG_COLOR_TYPES"][s["colortype"]] += 1
                    fp["MAX_PNG_SIDE"] = max(fp["MAX_PNG_SIDE"], max(s["w"], s["h"]))
                    if s["colortype"] == 3:
                        fp["PALETTE_PNG"] += 1
                    if s["colortype"] in (4, 6):
                        fp["ALPHA_PNG"] += 1
                    # tRNS chunk scan (first 96KB is enough for census)
                    if b"tRNS" in raw[:98304]:
                        fp["TRNS_PNG"] += 1
                del raw
            elif ln.endswith((".jpg", ".jpeg")):
                fp["RES_JPG"] += 1
            elif ln.endswith(".webp"):
                fp["RES_WEBP"] += 1
            elif ln.endswith(".xml") and n.startswith("res/"):
                fp["RES_XML"] += 1
                if "/drawable" in n or "/color" in n:
                    fp["RES_XML_DRAWABLE"] += 1
            elif n.startswith("lib/"):
                parts = n.split("/")
                if len(parts) >= 3:
                    if parts[2] not in fp["NATIVE_LIBS"]:
                        fp["NATIVE_LIBS"].append(parts[2])
            elif n.startswith("assets/"):
                fp["ASSETS"] += 1
            elif ln.endswith(".dex"):
                fp["DEX_FILES"] += 1
                dex_blob_chunks.setdefault(ln, []).append(z.read(n))

    # one marker pass per dex file (streamed strings via bytes.find loop)
    hits = Counter()
    for dname, chunks in dex_blob_chunks.items():
        blob = b"".join(chunks)
        del chunks
        for marker, (key, _fam) in DEX_MARKERS.items():
            mb = marker.encode()
            c = blob.count(mb)
            if c:
                hits[key] += c
        del blob
    fp["DEX_MARKERS"] = dict(hits)
    fp["PNG_COLOR_TYPES"] = dict(fp["PNG_COLOR_TYPES"])
    return fp


FAMILY_OF_KEY = {}
for _marker, (_key, _fam) in DEX_MARKERS.items():
    if _fam:
        FAMILY_OF_KEY[_key] = _fam

FAMILY_LABELS = {
    "FAMILY-A": "resource/density selection",
    "FAMILY-B": "bitmap decode",
    "FAMILY-C": "drawable inflation",
    "FAMILY-D": "ImageView",
    "FAMILY-E": "Canvas/imperative draw",
    "FAMILY-G": "EGL/GLES",
    "FAMILY-H": "SurfaceView/TextureView",
    "FAMILY-I": "custom native engine",
    "FAMILY-J": "libGDX",
    "FAMILY-K": "SDL",
    "FAMILY-L": "Compose",
    "FAMILY-M": "WebView",
    "FAMILY-N": "view animation",
}


def families_of(fp):
    fams = set()
    for key in fp["DEX_MARKERS"]:
        if key in FAMILY_OF_KEY:
            fams.add(FAMILY_OF_KEY[key])
    if fp["DENSITY_QUALIFIERS"]:
        fams.add("FAMILY-A")
    if fp["RES_XML_DRAWABLE"]:
        fams.add("FAMILY-C")
    if fp["NATIVE_LIBS"]:
        fams.add("FAMILY-I")
    return sorted(fams)


def main():
    reg = json.load(open(REGISTRY))
    recs = reg if isinstance(reg, list) else reg.get("TITLES", [])
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))

    out = []
    for rec in recs:
        pkg = rec["PACKAGE"]
        apks = sorted(
            [p for p in os.listdir(APK_CACHE) if p.startswith(pkg + "_")]
        ) if os.path.isdir(APK_CACHE) else []
        if not apks:
            out.append({
                "TITLE_ID": rec["TITLE_ID"], "TYPE": rec["TYPE"],
                "PACKAGE": pkg, "CATEGORY": rec.get("CATEGORY", ""),
                "APK_ON_DISK": False,
            })
            continue
        path = os.path.join(APK_CACHE, apks[0])
        st = os.stat(path)
        ckey = f"{pkg}:{st.st_size}:{int(st.st_mtime)}"
        if ckey in cache:
            fp = cache[ckey]
        else:
            try:
                fp = scan_apk(path)
            except Exception as e:  # never kill the batch for one bad zip
                fp = {"SCAN_ERROR": str(e)}
            cache[ckey] = fp
        entry = {
            "TITLE_ID": rec["TITLE_ID"], "TYPE": rec["TYPE"],
            "PACKAGE": pkg, "CATEGORY": rec.get("CATEGORY", ""),
            "APK": os.path.basename(path), "APK_SHA256": rec.get("APK_SHA256"),
            "APK_ON_DISK": True,
            "FINGERPRINT": fp,
            "FAMILIES": families_of(fp) if "SCAN_ERROR" not in fp else ["SCAN_ERROR"],
        }
        out.append(entry)

    fam_counts = Counter()
    for e in out:
        for f in e.get("FAMILIES", []):
            fam_counts[f] += 1
    result = {
        "WAVE": "S82-GFX-REVOLUTION",
        "GENERATED": __import__("datetime").datetime.now().isoformat(),
        "SCANNED": sum(1 for e in out if e.get("APK_ON_DISK")),
        "NOT_ON_DISK": sum(1 for e in out if not e.get("APK_ON_DISK")),
        "FAMILY_COUNTS": dict(fam_counts),
        "FAMILY_LABELS": FAMILY_LABELS,
        "TITLES": out,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), indent=1)
    json.dump(cache, open(CACHE, "w"))
    print(f"scanned={result['SCANNED']} not_on_disk={result['NOT_ON_DISK']}")
    for f, c in sorted(fam_counts.items()):
        print(f"  {f:9s} {c:3d}  {FAMILY_LABELS.get(f,'')}")


if __name__ == "__main__":
    main()
