#!/usr/bin/env python3
"""S188 W5-1f: disassemble Lb0/k;-><init>(I)V — the merged bucket ctor."""
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

bk = classes['Lb0/k;']
for m in bk.get_methods():
    if m.get_name() == '<init>':
        dump_method(bk, m, 100)

# also: who calls Lb1/t0;->A (findFragmentById) — find invoke sites of A(I)
print("\n=== callers of Lb1/t0;->A(I) and B(String) ===")
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        try:
            for ins in code.get_bc().get_instructions():
                s = str(ins.get_operands())
                if 'Lb1/t0;->A(I' in s or 'Lb1/t0;->B(Ljava/lang/String;' in s:
                    print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()}  {ins.get_name()}  {s[:90]}")
        except Exception:
            pass
