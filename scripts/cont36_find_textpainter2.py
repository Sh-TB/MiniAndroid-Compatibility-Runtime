#!/usr/bin/env python3
"""CONT-36 Phase 3f: enumerate EVERY class declaring methods named
drawText/drawTextRun/drawTextBlob, and EVERY call site (any invoke flavor)
targeting a method named drawText/drawTextRun."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

declarers = {}
callers = []
for c in d.get_classes():
    for m in c.get_methods():
        if m.get_name() in ("drawText", "drawTextRun", "drawTextBlob"):
            declarers.setdefault(c.get_name(), []).append(
                (m.get_name(), m.get_descriptor()))
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm:
                    continue
                out = ins.get_output()
                tm = (out.split("->")[1].split(":")[0].split("(")[0]
                      if "->" in out else "")
                if tm in ("drawText", "drawTextRun", "drawTextBlob"):
                    callers.append((m.get_class_name(), m.get_name(), nm,
                                    out.strip()[:110]))
        except Exception:
            continue

print("== classes declaring drawText-family methods ==")
for cls, ms in sorted(declarers.items()):
    print(f"  {cls}: {len(ms)} methods")
print()
print(f"== ALL call sites (any invoke flavor): {len(callers)} ==")
for x in callers[:40]:
    print(x)
