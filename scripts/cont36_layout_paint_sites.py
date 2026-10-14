#!/usr/bin/env python3
"""CONT-36 Phase 3i: find Layout/StaticLayout.paint(Canvas) call sites —
the F-NEW-297 field-ref-exact contract from AndroidParagraph.paint."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))
callers = []
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "->paint(" in out and "Landroid/text/" in out:
                    callers.append((m.get_class_name(), m.get_name(),
                                    out.strip()[:110]))
        except Exception:
            continue
print(f"Layout/StaticLayout.paint call sites: {len(callers)}")
for x in callers[:15]:
    print(x)
