#!/usr/bin/env python3
"""S54 ChessClock root-cause probe — disassemble ChessClock.color + callers (§15)."""
import sys

from androguard.core.apk import APK
from androguard.core.dex import DEX

a = APK("/home/z/my-project/apk_cache/com.chessclock.android_29.apk")
d = DEX(a.get_file("classes.dex"))
cls_want = "Lcom/chessclock/android/ChessClock;"
methods = sys.argv[1:] or ["color", "setUpGame", "setClock"]

for c in d.get_classes():
    if c.get_name() != cls_want:
        continue
    print("=== static fields:", [(f.get_name(), f.get_descriptor()) for f in c.get_fields()
                                 if f.get_access_flags_string().find("static") >= 0][:12])
    for m in c.get_methods():
        if m.get_name() not in methods:
            continue
        print(f"\n--- {m.get_name()} {m.get_descriptor()} "
              f"access={m.get_access_flags_string()}")
        try:
            for ins in m.get_instructions():
                print(f"  {ins.get_name():22s} {ins.get_output()}")
        except Exception as e:  # noqa: BLE001
            print("  DISASM ERROR:", e)
