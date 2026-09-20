#!/usr/bin/env python3
"""S72-W2: F-142 first-divergence recon for fishrings ImageView src->bitmap.

Pipeline evidence (constitution #148):
  APK -> ARSC/AXML -> src attr ref_id -> drawable_file_for_resid equivalent
Returns machine-readable findings, no guessing.
"""
import sys, zipfile, io, json
from androguard.core.bytecodes.axml import AXMLPrinter
from androguard.core.bytecodes.axml import ARSCParser

APK = "/home/z/my-project/upload/canonical_apks/fishrings_v1.23_vc6.apk"

a = ARSCParser(zipfile.ZipFile(APK).read("resources.arsc"))
z = zipfile.ZipFile(APK)

# 1. layout res used by GameActivity: 0x7f020001 (from [U007-INFLATE])
layout_name = a.get_resource(0x7f020001)
print("layout 0x7f020001 ->", layout_name)

# resolve via res_id
try:
    pkg, rtype, name = a.get_resource_name(0x7f020001)[:3]
    print("name:", pkg, rtype, name)
except Exception as e:
    print("resname err", e)

layouts = [n for n in z.namelist() if n.startswith("res/layout") and n.endswith(".xml")]
print("layout files:", layouts[:20])

# 2. parse the game layout XML: find all ImageView src attrs
target = None
for l in layouts:
    data = z.read(l)
    xml = AXMLPrinter(data).get_xml().decode("utf-8", "replace")
    if "ImageView" in xml:
        print(f"\n=== {l} contains ImageView ===")
        target = (l, xml)

if target:
    import re
    xml = target[1]
    # print every ImageView element line
    for m in re.finditer(r"<ImageView[^>]*>", xml):
        print(m.group(0)[:300])
    # count src attrs
    srcs = re.findall(r'android:src="([^"]+)"', xml)
    print("\nandroid:src values:", srcs)
    srccompat = re.findall(r'app:srcCompat="([^"]+)"', xml)
    print("srcCompat values:", srccompat)
    # backgrounds too
    bgs = re.findall(r'android:background="([^"]+)"', xml)
    print("android:background values:", bgs)

# 3. ARSC drawable table summary
print("\n=== drawable entries (first 30) ===")
try:
    for pkgname in a.get_packages_names():
        table = a.get_package(pkgname)
        for rtype in table:
            if "drawable" in str(rtype):
                print("type:", rtype)
                break
except Exception as e:
    print("arsc walk err:", e)

# list drawable files in zip
draw_files = [n for n in z.namelist() if n.startswith("res/drawable") or n.startswith("res/mipmap")]
print("\ndrawable/mipmap files (count=%d, first 25):" % len(draw_files))
for d in draw_files[:25]:
    print(" ", d)
