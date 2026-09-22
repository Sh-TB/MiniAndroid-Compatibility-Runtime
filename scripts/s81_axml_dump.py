#!/usr/bin/env python3
"""s81_axml_dump.py — dump binary AXML layouts of an APK (views + src/background
attrs) to prove whether the app's own XML actually references images/colors
(resource-side ground truth for the §21 provenance chain)."""
import sys
from androguard.core.axml import AXMLPrinter
from androguard.core.apk import APK

apk_path = sys.argv[1]
a = APK(apk_path)
layouts = [n for n in a.get_files() if n.startswith("res/layout") and n.endswith(".xml")]
print(f"layouts: {len(layouts)}")
for lx in layouts[:6]:
    try:
        data = a.get_file(lx)
        xml = AXMLPrinter(data).get_xml().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"-- {lx}: ERROR {e}")
        continue
    # compact: only lines with ImageView/src/background/textColor/drawable
    interesting = []
    for line in xml.splitlines():
        s = line.strip()
        if any(k in s for k in ("<ImageView", "ImageButton", "src=", "background=",
                                 "textColor=", "ListView", "RecyclerView", "TextView",
                                 "Button", "drawable", "textSize")):
            interesting.append(s[:200])
    print(f"\n===== {lx} ({len(xml)} bytes) =====")
    for s in interesting[:40]:
        print(" ", s)
