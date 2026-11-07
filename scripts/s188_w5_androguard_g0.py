#!/usr/bin/env python3
"""S188 W5-1g: disassemble Lb1/g0; (FragmentLayoutInflaterFactory)."""
from loguru import logger; logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

a = APK('/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk')
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

def dump_method(c, m, max_ins=250):
    print(f"\n=== {c.get_name()}->{m.get_name()}{m.get_descriptor()} ===")
    code = m.get_code()
    if not code:
        print("  (no code)")
        return
    for i, ins in enumerate(code.get_bc().get_instructions()):
        if i >= max_ins:
            print("  ...TRUNC")
            break
        ops = ', '.join(str(o) for o in ins.get_operands())
        print(f"  {i:3d} {ins.get_name():24s} {ops}")

g0 = classes['Lb1/g0;']
print("g0 fields:", [(f.get_name(), f.get_descriptor()) for f in g0.get_fields()])
print("g0 methods:", [f"{m.get_name()}{m.get_descriptor()}" for m in g0.get_methods()])
for m in g0.get_methods():
    if m.get_name() == '<init>' or m.get_name() == 'onCreateView':
        dump_method(g0, m, 120)
