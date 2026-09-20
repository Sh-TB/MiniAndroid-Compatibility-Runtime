#!/usr/bin/env python3
"""S72-W3 F-141 follow-up: disassemble Lim;.onCreate (FragmentManager null
producer hunt) + Lmc1;.b (findFragmentByTag consumer)."""
import zipfile
try:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX
except ImportError:
    from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk"
TARGETS = {("Lim;", "onCreate"), ("Lmc1;", "b")}

with zipfile.ZipFile(APK) as z:
    dex_data = {n: z.read(n) for n in z.namelist() if n.endswith(".dex")}

for dname, raw in dex_data.items():
    d = DEX(raw)
    try:
        methods = []
        for c in d.get_classes():
            methods.extend(c.get_methods())
    except AttributeError:
        methods = d.get_methods()
    for m in methods:
        key = (m.get_class_name(), m.get_name())
        if key in TARGETS:
            code = m.get_code()
            print(f"\n=== {key[0]}->{key[1]}{m.get_descriptor()} ({dname}) ===")
            if code is None:
                print("  <abstract/native>")
                continue
            pc = 0
            for ins in code.get_bc().get_instructions():
                ops = []
                for o in ins.get_operands():
                    if o[0] == 0:
                        ops.append(f"v{o[1]}")
                    else:
                        ops.append(str(o[1]))
                print(f"  {pc:5d}: {ins.get_name()} {' '.join(ops)}")
                pc += ins.get_length()
