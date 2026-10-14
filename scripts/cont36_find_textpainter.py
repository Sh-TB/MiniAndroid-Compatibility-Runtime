#!/usr/bin/env python3
"""CONT-36 Phase 3e: find the text PAINT class — classes whose methods both
reference android.graphics.Canvas and Lce1 (AndroidParagraph), then
disassemble the paint-shaped methods. Also answer: does ANY method in the
APK invoke Canvas.drawText through the Compose Canvas INTERFACE (Ld2; or
similar ifaces) — list the interface owner of drawText."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

cand = []
for c in d.get_classes():
    has_canvas = False
    has_ce1 = False
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            desc = m.get_descriptor()
            refs_canvas = "Landroid/graphics/Canvas;" in desc
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "Lce1;" in out:
                    has_ce1 = True
                if refs_canvas:
                    has_canvas = True
        except Exception:
            continue
        if refs_canvas and ("Lce1;" in desc or has_ce1):
            pass
    if has_canvas and has_ce1:
        cand.append(c.get_name())

print("classes referencing Canvas(in sig) AND calling Lce1:", cand[:20])

# The Compose Canvas interface: find the interface that declares drawText
# (owner of the Lkd1 implementation).
iface_decl = []
for c in d.get_classes():
    try:
        if "Interface" not in str(c.get_access_flags()) and \
           (c.get_access_flags() & 0x200) == 0:
            continue
    except Exception:
        continue
    for m in c.get_methods():
        if m.get_name() == "drawText" or m.get_name() == "drawTextRun":
            iface_decl.append((c.get_name(), m.get_name(), m.get_descriptor()))
print("interfaces declaring drawText/drawTextRun:", iface_decl[:10])

# who CALLS that interface's drawText (invoke-interface)?
callers = []
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke-interface" not in nm:
                    continue
                out = ins.get_output()
                meth = (out.split("->")[1].split(":")[0].split("(")[0]
                        if "->" in out else "")
                if meth in ("drawText", "drawTextRun"):
                    callers.append((m.get_class_name(), m.get_name(), out.strip()[:110]))
        except Exception:
            continue
print(f"== invoke-interface drawText/drawTextRun sites: {len(callers)} ==")
for x in callers[:20]:
    print(x)
