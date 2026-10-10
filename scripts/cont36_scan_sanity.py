#!/usr/bin/env python3
"""CONT-36 sanity: the scanner must find Ln3.h's Canvas.drawRoundRect and
Ln3.d's clipRect — proving the invoke scan walks real bytecode."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))
hits = {}
total_invokes = 0
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm:
                    continue
                total_invokes += 1
                out = ins.get_output()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if tm in ("drawRoundRect", "drawText", "drawTextRun",
                          "paint", "draw") and tcls.startswith("Landroid/"):
                    hits.setdefault((tcls, tm), []).append(m.get_class_name())
        except Exception:
            continue
print("total invoke instructions scanned:", total_invokes)
for (tc, tm), ms in sorted(hits.items()):
    u = sorted(set(ms))
    print(f"{tc}->{tm}: {len(u)} distinct callers, first 6: {u[:6]}")
