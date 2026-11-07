#!/usr/bin/env python3
"""S188 W5-1e: disassemble Lb1/t0;-><init>()V, Lb1/a1;->i()V, FragmentContainerView ctors."""
from loguru import logger; logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

a = APK('/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk')
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

def dump_method(c, m, max_ins=200):
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

fmc = classes['Lb1/t0;']
for m in fmc.get_methods():
    if m.get_name() == '<init>':
        dump_method(fmc, m, 120)

a1 = classes['Lb1/a1;']
for m in a1.get_methods():
    if m.get_name() == 'i':
        dump_method(a1, m, 80)

fcv = classes.get('Landroidx/fragment/app/FragmentContainerView;')
if fcv:
    print(f"\nFCV super: {fcv.get_superclassname()}")
    print("FCV methods:", [f"{m.get_name()}{m.get_descriptor()}" for m in fcv.get_methods()])
    for m in fcv.get_methods():
        if m.get_name() == '<init>':
            dump_method(fcv, m, 80)
