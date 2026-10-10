#!/usr/bin/env python3
"""CONT-36 Phase 3l: decode Lg6 (the Layout.draw caller) — full method list,
the draw method body (field-ref-exact), and who calls Lg6 methods. Also:
does the csw run log contain Lg6 entries at all?"""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

print("=== Lg6 class ===")
for c in d.get_classes():
    if c.get_name() != "Lg6;":
        continue
    print("  super:", c.get_superclassname(), "ifaces:", c.get_interfaces())
    for f in c.get_fields():
        print("  field:", f.get_name(), f.get_descriptor())
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        body_has_draw = False
        ins_list = []
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if "invoke" in nm:
                ins_list.append((pc, nm, out[:120]))
                if "Layout;->draw" in out or "Layout;->paint" in out:
                    body_has_draw = True
            pc += ins.get_length()
        if body_has_draw:
            print(f"  --- {m.get_name()} {m.get_descriptor()} ---")
            for p, nm, out in ins_list:
                print(f"    pc={p} {nm} {out}")

# callers of Lg6 methods
callers = {}
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                if tcls == "Lg6;":
                    tm = out.split("->")[1].split(":")[0].split("(")[0]
                    callers.setdefault(tm, []).append(
                        f"{m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue
print("=== callers of Lg6 methods ===")
for tm, cs in sorted(callers.items()):
    print(f"  Lg6.{tm}: {sorted(set(cs))[:6]}")
