#!/usr/bin/env python3
"""CONT-36 Phase 3j: Lce1 fields + <init>/b() bodies; find where the
StaticLayout is stored and whether ANY method returns it (the paint source)."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk"
z = zipfile.ZipFile(APK)
d = DEX(z.read("classes.dex"))

for c in d.get_classes():
    if c.get_name() != "Lce1;":
        continue
    print("=== Lce1 fields ===")
    for f in c.get_fields():
        print("  ", f.get_name(), f.get_descriptor())
    for m in c.get_methods():
        if m.get_name() not in ("<init>", "b", "i"):
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"--- {m.get_name()} {m.get_descriptor()} ---")
        pc = 0
        for ins in m.get_instructions():
            nm = ins.get_name()
            out = ins.get_output()
            if ("invoke" in nm or "iget" in nm or "iput" in nm or
                    "sget" in nm or nm.startswith("const") or
                    nm.startswith("return") or "new-instance" in nm or
                    "check-cast" in nm):
                print(f"  pc={pc} {nm} {out[:130]}")
            pc += ins.get_length()

# ALSO: the Paragraph interface Lgb — its method list (the renamed paint?)
for c in d.get_classes():
    if c.get_name() != "Lgb;":
        continue
    print("=== Lgb (Paragraph iface) methods ===")
    for m in c.get_methods():
        print("  ", m.get_name(), m.get_descriptor())
