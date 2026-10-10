#!/usr/bin/env python3
"""CONT-36: dump Lvv interface methods (the Compose GraphicsLayer iface —
R8-renamed), Lz40 method list, and the body of Lvv.d (the 46× draw-window
method) — is it the layer draw that should composite?"""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    nm = c.get_name()
    if nm == "Lvv;":
        print("=== Lvv (interface?) ===", c.get_superclassname(),
              c.get_interfaces())
        for m in c.get_methods():
            print(f"  {m.get_name()} {m.get_descriptor()}")
    if nm == "Lz40;":
        print("=== Lz40 methods ===")
        for m in c.get_methods():
            code = m.get_code()
            sz = code.get_insns_size() if code else 0
            print(f"  {m.get_name()} {m.get_descriptor()} size={sz}")
    if nm == "Lt40;":
        print("=== Lt40 methods (the block iface?) ===",
              c.get_superclassname(), c.get_interfaces())
        for m in c.get_methods():
            print(f"  {m.get_name()} {m.get_descriptor()}")
