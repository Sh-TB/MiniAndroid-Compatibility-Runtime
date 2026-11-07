#!/usr/bin/env python3
"""S188 W6: androguard ground truth for the two W6 walls.

W6-1  CoordinatorLayout.t ISE "Could not find CoordinatorLayout descendant
      view with id null to anchor view" -> which class/method throws, which
      LayoutParams field is the anchorId, which styleable slot the
      LayoutParams.<init>(ctx,attrs) reads for layout_anchor /
      layout_anchorGravity, and the resolved attr resource ids.
W6-2  Landroidx/lifecycle/h0;.a NPE "Insets.left on null" -> disassemble h0.a,
      find the field read, and trace the caller that needs
      View.getRootWindowInsets() to be non-null.
"""
import re
import json
from pathlib import Path
from loguru import logger
logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = '/home/z/my-project/upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = Path('/home/z/my-project/evidence/s188_w6')
OUT.mkdir(parents=True, exist_ok=True)

a = APK(APK_PATH)
d = DEX(a.get_dex())
classes = {c.get_name(): c for c in d.get_classes()}
print(f"apk={APK_PATH} classes={len(classes)}")

findings = {}

# ---------------------------------------------------------------- W6-1
# 1) locate the ISE thrower by string
needle = 'Could not find CoordinatorLayout descendant view'
thrower_cls = thrower_m = None
for s in d.get_strings():
    if needle in s:
        print('STRING:', s[:120])

for cn, c in classes.items():
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        try:
            for ins in code.get_bc().get_instructions():
                if 'const-string' in ins.get_name():
                    op = ins.get_operands()
                    if len(op) >= 2 and needle in str(op[-1]):
                        thrower_cls, thrower_m = cn, m
                        print(f"THROWER {cn}->{m.get_name()}{m.get_descriptor()}")
                        break
            if thrower_cls:
                break
        except Exception:
            continue
    if thrower_cls:
        break

def dump_method(c, m, max_ins=80, tag=''):
    print(f"\n=== {tag}{c.get_name()}->{m.get_name()}{m.get_descriptor()} ===")
    code = m.get_code()
    if not code:
        print('  (no code)')
        return
    out = []
    n = 0
    for ins in code.get_bc().get_instructions():
        if n >= max_ins:
            out.append('  ...')
            break
        ops = ', '.join(str(o) for o in ins.get_operands())
        out.append(f"  {ins.get_name():26s} {ops}")
        n += 1
    txt = '\n'.join(out)
    print(txt)
    return txt

if thrower_cls:
    findings['ise_thrower'] = dict(
        cls=thrower_cls, method=thrower_m.get_name(),
        desc=thrower_m.get_descriptor())
    dump_method(classes[thrower_cls], thrower_m, 120, 'W6-1 ISE ')

# 2) find CoordinatorLayout LayoutParams class (may be merged/renamed):
#    a class extending ViewGroup$MarginLayoutParams whose ctor reads
#    layout_anchor-ish attr ids; search by class name first.
co_cls = None
for cn in classes:
    if 'CoordinatorLayout' in cn:
        co_cls = cn
        print('COORD class present:', cn)
for cn in classes:
    if 'LayoutParams' in cn and ('Coordinator' in cn or cn.startswith('Lb')):
        pass

# 3) find R$styleable CoordinatorLayout_Layout array
style = {}
for cn, c in classes.items():
    if cn.endswith('R$styleable;'):
        for f in c.get_fields():
            if 'CoordinatorLayout' in f.get_name():
                print('STYLEABLE FIELD:', cn, f.get_name(), f.get_descriptor())

# dump the <clinit> of the R$styleable that defines CoordinatorLayout_Layout
if thrower_cls is None:
    print('ISE thrower NOT found by string scan')
else:
    tc = classes[thrower_cls]
    # the anchorId field: look for iget I in the thrower method
    anchor_fld = None
    code = thrower_m.get_code()
    for ins in code.get_bc().get_instructions():
        ops = ', '.join(str(o) for o in ins.get_operands())
        if ins.get_name().startswith('iget') and ' I' in ops:
            print('THROWER reads int field:', ops)

# 4) LayoutParams ctor: find classes whose ctor takes (Context, AttributeSet)
#    and reads sget of styleable arrays + TypedArray.getInt
params_cls = None
for cn, c in classes.items():
    desc = c.get_superclassname() or ''
    if 'MarginLayoutParams' in desc and cn not in ('Landroid/view/ViewGroup$MarginLayoutParams;',):
        ms = [m for m in c.get_methods()
              if m.get_name() == '<init>' and 'AttributeSet' in m.get_descriptor()]
        if ms and 'Coordinator' in cn:
            params_cls = cn
            print('COORD LayoutParams:', cn, desc)

# search styleable ints: find "layout_anchor" in strings
anchor_ids = [s for s in d.get_strings() if 'layout_anchor' in s]
print('layout_anchor strings:', anchor_ids[:8])

with open(OUT / 'w6_andro_anchor_probe.txt', 'w') as f:
    f.write(json.dumps(findings, indent=1))
print('\nsaved', OUT / 'w6_andro_anchor_probe.txt')
