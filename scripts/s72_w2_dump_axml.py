#!/usr/bin/env python3
"""S72-W2 F-142: dump fishrings AXML layouts via AXMLPrinter (string-pool only,
no ARSC needed). Evidence for ImageView src attr shape."""
import zipfile
from androguard.core.bytecodes.axml import AXMLPrinter

APK = "/home/z/my-project/upload/canonical_apks/fishrings_v1.23_vc6.apk"
z = zipfile.ZipFile(APK)
layouts = [n for n in z.namelist() if n.startswith("res/layout") and n.endswith(".xml")]
print("layouts:", layouts)
for l in layouts:
    try:
        xml = AXMLPrinter(z.read(l)).get_xml().decode("utf-8", "replace")
    except Exception as e:
        print(f"--- {l}: AXML fail {e}")
        continue
    print(f"\n########## {l} ({len(xml)} chars) ##########")
    print(xml[:6000])
