#!/usr/bin/env python3
"""CONT-36 Phase 3b: find the REAL text-paint call path in composeStopwatch —
every invoke of Canvas.drawText-family and the StaticLayout method family,
with the enclosing R8 classes. Uses the classes->methods iteration (the
androguard API that returns EncodedMethod with get_code())."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith(".dex")]
want_canvas = ("drawText", "drawTextRun", "drawTextBlob", "drawPosText")
canvas_hits = []
sl_methods = {}
n_classes = n_methods = 0

for dname in dex_names:
    d = DEX(z.read(dname))
    for c in d.get_classes():
        n_classes += 1
        for m in c.get_methods():
            try:
                if m.get_code() is None:
                    continue
            except Exception:
                continue
            n_methods += 1
            try:
                for ins in m.get_instructions():
                    if "invoke" not in ins.get_name():
                        continue
                    out = ins.get_output()
                    meth_name = (out.split("->")[1].split(":")[0].split("(")[0]
                                 if "->" in out else "")
                    if "Landroid/graphics/Canvas;" in out and meth_name in want_canvas:
                        canvas_hits.append((m.get_class_name(), m.get_name(),
                                            out.strip()[:110]))
                    if "StaticLayout" in out:
                        meth = (out.split("->")[1].split(":")[0]
                                if "->" in out else "?")
                        sl_methods.setdefault(meth, []).append(
                            (m.get_class_name(), m.get_name()))
            except Exception:
                continue

print(f"classes={n_classes} methods_with_code={n_methods}")
print(f"== Canvas.drawText-family invokes: {len(canvas_hits)} ==")
for h in canvas_hits[:40]:
    print(h)
print()
print("== StaticLayout methods invoked (method -> #callers, examples) ==")
for meth, callers in sorted(sl_methods.items()):
    cs = sorted(set(f"{c[0]}.{c[1]}" for c in callers))[:4]
    print(f"  {meth}: {len(callers)} sites, e.g. {cs}")
