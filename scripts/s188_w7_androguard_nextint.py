#!/usr/bin/env python3
"""S188 W7: androguard ground truth for the nextInt-bound dimension chain.

Target chain (from W6 worklog):
  ×3 f086-nextint-bound IAE: Lu3/a;.c(II)I wrapper around
  ThreadLocalRandom.current().nextInt(origin, bound); caller
  MainActivity.w()V reads Toolbar/LinearLayout getWidth/getHeight —
  bound computed from a 0-dimension view.

Goal: DEX-level truth for
  (1) MainActivity.w()V — which getWidth/getHeight it reads, what arithmetic
      feeds the bound, and where the result goes (which method consumes it);
  (2) Lu3/a;.c — exact wrapper shape (origin/bound order, any guards);
  (3) who calls MainActivity.w()V and when (which lifecycle phase — i.e. why
      in real Android the views already have dimensions);
  (4) the view fields w() reads (R.id values) so the live trace can name them.
"""
import sys
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]
classes = {}
for d in dexes:
    for c in d.get_classes():
        classes[c.get_name()] = c

def dump_method(cn, mname, max_ins=400):
    c = classes.get(cn)
    if not c:
        print(f"!! class {cn} not found"); return
    for m in c.get_methods():
        if m.get_name() != mname:
            continue
        print(f"\n=== {cn}->{m.get_name()}{m.get_descriptor()}")
        code = m.get_code()
        if not code:
            print("  (abstract/native)"); continue
        try:
            ins_list = list(code.get_bc().get_instructions())
        except Exception as e:
            print("  ITER ERROR:", type(e).__name__, e); continue
        for n, ins in enumerate(ins_list[:max_ins]):
            op = ins.get_name()
            ops = ins.get_operands()
            def fmt(o):
                t, v = o[0], o[1]
                if isinstance(v, str) and len(v) > 72: return v[:72] + '…'
                return str(v)
            print(f"  {n:3d} {op:26s} {', '.join(fmt(o) for o in ops)}")
        if len(ins_list) > max_ins:
            print(f"  …({len(ins_list)-max_ins} more)")

def find_callers(cn, mname, desc=None):
    sig_head = f"{cn}->{mname}"
    out = []
    for k, c in classes.items():
        for m in c.get_methods():
            code = m.get_code()
            if not code: continue
            try:
                for ins in code.get_bc().get_instructions():
                    if ins.get_name().startswith('invoke'):
                        s = str(ins.get_operands())
                        if sig_head in s and (desc is None or desc in s):
                            out.append(f"{k}->{m.get_name()}{m.get_descriptor()}")
            except Exception:
                continue
    return sorted(set(out))

print("### 1. MainActivity.w()V")
dump_method('Ltibarj/tranquilstopwatch/MainActivity;', 'w')

print("\n### 2. callers of MainActivity.w")
for x in find_callers('Ltibarj/tranquilstopwatch/MainActivity;', 'w', ')V'):
    print("  ", x)

print("\n### 3. u3/a.c (nextInt wrapper)")
dump_method('Lu3/a;', 'c')

print("\n### 4. u3/a class overview")
c = classes.get('Lu3/a;')
if c:
    print("  super:", c.get_superclassname())
    for m in c.get_methods():
        print(f"   {m.get_access_flags_string():20s} {m.get_name()}{m.get_descriptor()}")
