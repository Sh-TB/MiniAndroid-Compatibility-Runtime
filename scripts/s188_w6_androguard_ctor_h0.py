#!/usr/bin/env python3
"""S188 W6-1b/2: b0/f LayoutParams ctor styleable slots + h0.a insets NPE."""
import json
from pathlib import Path
from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = Path('/home/z/my-project/evidence/s188_w6')

a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}

def dump_method(c, m, max_ins=200):
    print(f"\n=== {c.get_name()}->{m.get_name()}{m.get_descriptor()} ===")
    code = m.get_code()
    if not code:
        print('  (no code)')
        return
    n = 0
    for ins in code.get_bc().get_instructions():
        if n >= max_ins:
            print('  ...')
            break
        ops = ', '.join(str(o) for o in ins.get_operands())
        print(f"  {ins.get_name():26s} {ops}")
        n += 1

# ---- b0/f: find its ctors and superclass
b0f = classes.get('Lb0/f;')
if b0f:
    print('b0/f super:', b0f.get_superclassname())
    for m in b0f.get_methods():
        if m.get_name() == '<init>':
            dump_method(b0f, m, 260)
else:
    print('b0/f NOT FOUND')

# ---- CoordinatorLayout.n(View) -> returns b0/f (cast)
co = classes.get('Landroidx/coordinatorlayout/widget/CoordinatorLayout;')
if co:
    for m in co.get_methods():
        if m.get_name() == 'n':
            dump_method(co, m, 60)

# ---- W6-2: h0 class + a() method
h0 = classes.get('Landroidx/lifecycle/h0;')
if h0:
    print('\n\n######## h0 super:', h0.get_superclassname())
    for m in h0.get_methods():
        print(' h0 method:', m.get_name(), m.get_descriptor())
    for m in h0.get_methods():
        if m.get_name() == 'a':
            dump_method(h0, m, 200)
else:
    print('Landroidx/lifecycle/h0; NOT FOUND — search merged candidates')
    # find classes containing the string 'Insets' usage — search methods
    # whose code throws NPE after reading field named e/f (left/right)
    for cn, c in classes.items():
        if not cn.startswith('Landroidx/lifecycle/'):
            continue
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            txt = []
            try:
                for ins in code.get_bc().get_instructions():
                    if 'iget' in ins.get_name():
                        ops = str(ins.get_operands())
                        if ' I' in ops and ('->e ' in ops or '->f ' in ops):
                            txt.append(ops)
            except Exception:
                continue
            if txt:
                print(f'candidate {cn}->{m.get_name()}: {txt[:3]}')
