#!/usr/bin/env python3
"""CONT-94: find all callers of LaunchActivity;->H(V and ->z0(I)V across
all dex files; also any new-instance of LaunchActivity (who allocates #7307)."""
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

a = APK("upload/telegram_official.apk")
for dn in a.get_dex_names():
    raw = a.get_file(dn)
    if b"LaunchActivity" not in raw:
        continue
    d = DalvikVMFormat(raw)
    hits = []
    for c in d.get_classes():
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            addr = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                o = ins.get_output()
                if op.startswith("invoke") and (
                        "LaunchActivity;->H(" in o or
                        "LaunchActivity;->z0(I)" in o):
                    hits.append((c.get_name(), m.get_name(), m.get_descriptor(),
                                 addr, op, o))
                if op == "new-instance" and "LaunchActivity" in o:
                    hits.append((c.get_name(), m.get_name(), m.get_descriptor(),
                                 addr, op, o))
                addr += ins.get_length()
    if hits:
        print("=== dex %s ===" % dn)
        for h in hits:
            print("  %s.%s%s @%d: %s %s" % h)
