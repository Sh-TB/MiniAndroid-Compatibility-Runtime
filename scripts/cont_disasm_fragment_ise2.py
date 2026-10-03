#!/usr/bin/env python3
"""CONT-ROOT-C: locate the method holding the 'must be a public static class'
string and dump the check that guards it (which Class metadata calls precede
the throw)."""
import sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/diff366/hidden_sources/fr.arnaudguyon.spacevertex_29.apk"
NEEDLE = "must be a public static class"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            try:
                bc = code.get_bc()
                instrs = list(bc.get_instructions())
            except Exception:
                continue
            for ins in instrs:
                out = ins.get_output()
                if NEEDLE in out:
                    cls = c.get_name()
                    print(f"=== {cls}.{m.get_name()} {m.get_descriptor()} in {name} ===")
                    pc = 0
                    for ins2 in instrs:
                        o = ins2.get_output()
                        # print calls, igets, throws, consts of interest
                        if (ins2.get_name().startswith("invoke") or
                            ins2.get_name() in ("iget", "iget-object", "iget-boolean", "throw", "new-instance") or
                            "Class" in o or "Modifier" in o or "Member" in o or
                            NEEDLE in o or "canonical" in o.lower()):
                            print(f"pc={pc} {ins2.get_name()} {o}")
                        pc += ins2.get_length()
                    sys.exit(0)
print("needle not found")
