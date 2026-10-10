#!/usr/bin/env python3
"""CONT-36: callers of Lz40.d (the GraphicsLayer draw/composite) and the
callee's body — the never-fired RenderNode composite."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

# callers
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if out.startswith("Lz40;->d(") or out.startswith("Lxk0;->m(") \
                   or out.startswith("Lm3;->l("):
                    print("CALLER:", m.get_class_name(), m.get_name(),
                          "->", out.strip()[:100])
        except Exception:
            continue

# body of Lz40.d
for c in d.get_classes():
    if c.get_name() != "Lz40;":
        continue
    print("=== Lz40 super/ifaces:", c.get_superclassname(),
          c.get_interfaces())
    for m in c.get_methods():
        if m.get_name() != "d":
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"--- Lz40.d {m.get_descriptor()} ---")
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if "invoke" in nm or nm.startswith("return") or \
               "iget" in nm or "check-cast" in nm:
                print(f"  pc={pc} {nm} {out[:120]}")
            pc += ins.get_length()
