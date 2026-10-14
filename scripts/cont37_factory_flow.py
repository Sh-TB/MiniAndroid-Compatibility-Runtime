#!/usr/bin/env python3
"""CONT-37: Lqe1/Lld1 shapes + global search for d()Lok0; invocations
(any declared class) — the factory dispatch may be renamed/relayed."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

print("== Lqe1 / Lld1 shapes ==")
for c in d.get_classes():
    if c.get_name() in ("Lqe1;", "Lld1;"):
        print(f"  {c.get_name()} super={c.get_superclassname()} ifaces={list(c.get_interfaces())}")
        for m in c.get_methods():
            code = m.get_code()
            n = sum(1 for _ in m.get_instructions()) if code else 0
            print(f"     {m.get_access_flags_string():20s} {m.get_name()}{m.get_descriptor()} [{n}]")

print("\n== ALL invocations of d()Lok0; (any target class) ==")
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                if "invoke" not in nm:
                    continue
                out = ins.get_output().strip()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                rest = out.split("->")[1]
                tm = rest.split(":")[0].split("(")[0]
                tdesc = rest.split(":")[0]
                if tm == "d" and tdesc == "d()Lok0;":
                    print(" ", m.get_class_name(), m.get_name(), nm, "->", tcls + ";->d()Lok0;")
        except Exception:
            continue
