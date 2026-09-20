#!/usr/bin/env python3
"""S72-W3 F-141: disassemble the null-receiver NPE sites surfaced by the
f141 law in the dooz run — find the null PRODUCER (constitution §171).
Targets: Lwe;.run (Object.getClass null @42), Lxu;.<clinit> (Long.longValue
null @24), Lyu;.<clinit> (escape @0x14), Lvs;.<clinit>, Lfv;.<clinit>."""
import sys
try:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX  # androguard <4
except ImportError:
    from androguard.core.dex import DEX  # androguard 4.x

APK = "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"
TARGETS = [
    ("Lwe;", "run", 42),
    ("Lxu;", "<clinit>", 24),
    ("Lyu;", "<clinit>", 20),
    ("Lfv;", "<clinit>", 25),
    ("Lvs;", "<clinit>", 36),
]

import zipfile
with zipfile.ZipFile(APK) as z:
    dex_data = {n: z.read(n) for n in z.namelist() if n.endswith(".dex")}

for dname, raw in dex_data.items():
    d = DEX(raw)
    all_methods = []
    try:
        for c in d.get_classes():
            all_methods.extend(c.get_methods())
    except AttributeError:
        all_methods = d.get_methods()
    for m in all_methods:
        cls = m.get_class_name()
        mname = m.get_name()
        for (tc, tm, near_pc) in TARGETS:
            if cls == tc and mname == tm:
                code = m.get_code()
                print(f"\n=== {cls}->{mname}{m.get_descriptor()} ({dname}) ===")
                if code is None:
                    print("  <abstract/native>")
                    continue
                bc = code.get_bc()
                pc = 0
                for idx, ins in enumerate(bc.get_instructions()):
                    op = ins.get_name()
                    operands = ins.get_operands()
                    ops = []
                    for o in operands:
                        if o[0] == 0:  # register
                            ops.append(f"v{o[1]}")
                        elif o[0] == 1:  # literal
                            ops.append(str(o[1]))
                        else:
                            ops.append(str(o[1]))
                    mark = " <<<" if pc in (near_pc, 0x14, 24, 42) else ""
                    print(f"  {pc:6d}: {op} {' '.join(ops)}{mark}")
                    pc += ins.get_length()
