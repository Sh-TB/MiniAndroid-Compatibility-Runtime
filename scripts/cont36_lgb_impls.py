#!/usr/bin/env python3
"""CONT-36 Phase 3k: find every class implementing Lgb (the Compose
Paragraph interface) and every method anywhere taking a Canvas first param
whose body references a Layout field — the R8-renamed paint. Also dump
Lgb's method names."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

print("=== Lgb methods ===")
for c in d.get_classes():
    if c.get_name() == "Lgb;":
        for m in c.get_methods():
            print("  ", m.get_name(), m.get_descriptor())

print("=== classes implementing Lgb ===")
impls = []
for c in d.get_classes():
    try:
        ifaces = c.get_interfaces()
    except Exception:
        continue
    if "Lgb;" in ifaces:
        impls.append(c.get_name())
        ms = [(m.get_name(), m.get_descriptor()) for m in c.get_methods()]
        canvas_ms = [x for x in ms if "Landroid/graphics/Canvas;" in x[1]]
        print(f"  {c.get_name()}: {len(ms)} methods, canvas-taking: {canvas_ms}")
print("all impls:", impls)
