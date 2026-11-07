#!/usr/bin/env python3
"""S188 W5-1d: raw disassembly of Lb1/t0;->A(I) and friends."""
from loguru import logger; logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

a = APK('/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk')
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}
FM = 'Lb1/t0;'
fmc = classes[FM]

def dump_method(c, m, max_ins=60):
    print(f"\n=== {c.get_name()}->{m.get_name()}{m.get_descriptor()} ===")
    code = m.get_code()
    if not code:
        print("  (no code)")
        return
    n = 0
    for ins in code.get_bc().get_instructions():
        if n >= max_ins:
            print("  ...")
            break
        ops = ', '.join(str(o) for o in ins.get_operands())
        print(f"  {ins.get_name():28s} {ops}")
        n += 1

# A(I) = findFragmentById per W4 evidence
for m in fmc.get_methods():
    if m.get_name() == 'A':
        dump_method(fmc, m, 40)

# find which b1/t0 method writes/reads any field of type Lb0/k;
print("\n=== b1/t0 methods touching any Lb0/k; field ===")
for m in fmc.get_methods():
    code = m.get_code()
    if not code: continue
    try:
        cnt = 0
        for ins in code.get_bc().get_instructions():
            s = str(ins.get_operands())
            if 'Lb0/k;' in s:
                cnt += 1
        if cnt:
            print(f"  {m.get_name()}{m.get_descriptor()}  b0k_refs={cnt}")
    except Exception:
        pass

# and in the whole DEX: iget-object vA, vB, field:Lb1/t0;->c: raw format check
print("\n=== global raw 'Lb1/t0;->c' substring scan (any op) ===")
total = 0
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        try:
            for ins in code.get_bc().get_instructions():
                if 'Lb1/t0;->c' in str(ins.get_operands()):
                    total += 1
                    if total <= 12:
                        print(f"  {c.get_name()}->{m.get_name()}{m.get_descriptor()}  {ins.get_name()}  {str(ins.get_operands())[:100]}")
        except Exception:
            pass
print("total refs to Lb1/t0;->c:", total)
