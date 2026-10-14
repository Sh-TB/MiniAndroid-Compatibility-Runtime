#!/usr/bin/env python3
"""CONT-36 Phase 3: decode the Compose text-paint call path in
composeStopwatch (v1.9.1 vc1009011) — find every invoke of
Layout.draw(StaticLayout.draw(Canvas)) and the enclosing R8 classes,
so the F-NEW-297 law is field-ref-exact."""
import zipfile, sys
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"

z = zipfile.ZipFile(APK)
dexes = {}
for n in z.namelist():
    if n.endswith(".dex"):
        dexes[n] = DEX(z.read(n))

targets = ("Landroid/text/StaticLayout;", "Landroid/text/Layout;")
hits = []
for dname, d in dexes.items():
    for m in d.get_methods():
        if m.get_descriptor() is None or not hasattr(m, "get_instructions"):
            continue
        try:
            code = m.get_code()
        except Exception:
            continue
        if not code:
            continue
        try:
            bc = list(m.get_instructions())
        except Exception:
            continue
        for ins in bc:
            op = ins.get_name()
            if "invoke" not in op:
                continue
            out = ins.get_output()
            if "Landroid/text/StaticLayout;" in out and " draw" in out:
                hits.append((dname, m.get_class_name(), m.get_name(),
                             m.get_descriptor(), op, out.strip()[:120]))

print(f"== invoke sites of StaticLayout.draw: {len(hits)} ==")
for h in hits[:20]:
    print(h)

# also: who calls Layout;.draw (the superclass entry)?
hits2 = []
for dname, d in dexes.items():
    for m in d.get_methods():
        if not hasattr(m, "get_instructions"):
            continue
        try:
            code = m.get_code()
        except Exception:
            continue
        if not code:
            continue
        try:
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "Landroid/text/Layout;" in out and " draw" in out:
                    hits2.append((m.get_class_name(), m.get_name(), out.strip()[:120]))
        except Exception:
            continue
print(f"== invoke sites of Layout.draw: {len(hits2)} ==")
for h in hits2[:20]:
    print(h)
