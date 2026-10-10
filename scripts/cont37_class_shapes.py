#!/usr/bin/env python3
"""CONT-37 Phase 1: dump the full class shapes of Lte1, Lod1, Lg6, Lr40,
Loc0 — super, interfaces, every method with descriptor — so the INTERFACE
dispatch (rename-hidden drawText entry) can be identified."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

TARGETS = {"Lte1;", "Lod1;", "Lg6;", "Lr40;", "Loc0;"}

for c in d.get_classes():
    if c.get_name() in TARGETS:
        print(f"=== {c.get_name()} super={c.get_superclassname()} ifaces={list(c.get_interfaces())} ===")
        for m in sorted(c.get_methods(), key=lambda m: (m.get_name(), m.get_descriptor())):
            code = m.get_code()
            n_ins = 0
            if code:
                n_ins = sum(1 for _ in m.get_instructions())
            print(f"  {m.get_access_flags_string():24s} {m.get_name()}{m.get_descriptor()}  [{n_ins} ins]")
        print()
