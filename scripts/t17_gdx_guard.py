#!/usr/bin/env python3
"""T17: disassemble libGDX load-guard chain from tower3d classes.dex."""
import zipfile, sys
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/stack.tower3d_1.apk"
z = zipfile.ZipFile(APK)
dex = DEX(z.read("classes.dex"))

TARGETS = [
    "Lcom/badlogic/gdx/backends/android/AndroidApplicationConfiguration$1;",
    "Lcom/badlogic/gdx/utils/SharedLibraryLoader;",
    "Lcom/badlogic/gdx/utils/GdxNativesLoader;",
]

for m in dex.get_methods():
    cls = m.get_class_name()
    if cls not in TARGETS:
        continue
    name = m.get_name()
    if cls.endswith("$1;") and name not in ("load", "<init>"):
        continue
    if cls == "Lcom/badlogic/gdx/utils/SharedLibraryLoader;" and name not in ("load", "loadLibrary", "extractLibrary", "<init>"):
        continue
    if cls == "Lcom/badlogic/gdx/utils/GdxNativesLoader;" and name not in ("load", "<clinit>", "<init>"):
        continue
    print(f"\n=== {cls} -> {name}{m.get_descriptor()}")
    code = m.get_code()
    if code is None:
        print("  (abstract/native)")
        continue
    # catch handlers
    tries = code.get_tries() if hasattr(code, "get_tries") else []
    try:
        handlers = code.get_handlers()
        print("  handlers:", handlers)
    except Exception as e:
        print("  handlers err:", e)
    for ins in m.get_instructions():
        op = ins.get_name()
        if op in ("invoke-virtual", "invoke-static", "invoke-direct", "invoke-super"):
            buf = ins.get_output()
            print(f"  {op} {buf[:100]}")
        elif op.startswith("move-exception") or "catch" in op:
            print(f"  {op}")
    # print try/catch ranges via raw tries table
