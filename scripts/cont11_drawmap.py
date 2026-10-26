#!/usr/bin/env python3
"""CONT-11 W7: map the dooz Compose DRAW chain around the AndroidCanvas bridge.

Known from W4/W6:
  Lt4;  = AndroidComposeView (root view; layers drawContent ran x42)
  Lel0; = LayoutNode;  Lpz0;/Lug0; = layer family;  Ljt1; = AndroidCanvas
  Frontier: layer drawContent chains run (Lpz0;.M0/L0/T0 x42) but Ljt1;
  is NEVER constructed -> 0 canvas ops.

This script answers, straight from the DEX:
  Q1: which methods contain `new-instance Ljt1;` (the Canvas factory sites)?
  Q2: what does Lt4; onDraw/dispatchDraw call (the draw entry chain)?
  Q3: what do Lpz0;.M0/L0/T0 call (the layer drawContent family)?
  Q4: who constructs the canvas holder / Canvas factory helpers?
"""
import sys, zipfile, re
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

def load_dexs():
    out = []
    with zipfile.ZipFile(APK) as z:
        names = [n for n in z.namelist() if re.match(r'classes\d*\.dex$', n)]
        for n in sorted(names):
            out.append((n, DalvikVMFormat(z.read(n))))
    return out

print("loading dex...")
dexs = load_dexs()
print(f"loaded {len(dexs)} dex files")

# index classes by name
cls = {}
for n, d in dexs:
    for c in d.get_classes():
        cls[c.get_name()] = (n, c)

def find_class(name):
    return cls.get(name)

def method_insns(m):
    code = m.get_code()
    if not code:
        return []
    return code.get_bc().get_instructions()

def calls_of(m):
    out = []
    for i in method_insns(m):
        op = i.get_name()
        if 'invoke' in op:
            try:
                ref = i.get_operands()
                # last operand holds the method ref
                s = i.get_output()
                out.append((op, s))
            except Exception:
                pass
    return out

# ---------- Q1: new-instance Ljt1; sites ----------
print("\n=== Q1: methods containing new-instance Ljt1; or invoke Ljt1;.<init> ===")
hits = 0
for cname, (n, c) in cls.items():
    for m in c.get_methods():
        txt = None
        for i in method_insns(m):
            s = i.get_output()
            if 'Ljt1;' in s and ('new-instance' in i.get_name() or 'invoke-direct' in i.get_name() or 'invoke-static' in i.get_name()):
                if txt is None:
                    txt = f"{cname}->{m.get_name()}{m.get_descriptor()}"
                    print(f"  {txt}")
                    hits += 1
                # first matching instruction detail
                print(f"      {i.get_name():14s} {s[:150]}")
                break
        if hits > 40:
            break
    if hits > 40:
        break
if hits == 0:
    print("  (none found — Ljt1; ctor is reached some other way)")

# ---------- Q2: Lt4; draw entries ----------
print("\n=== Q2: Lt4; (AndroidComposeView) draw-related methods ===")
_, c = find_class('Lt4;')
for m in c.get_methods():
    nm = m.get_name()
    if nm in ('onDraw', 'dispatchDraw', 'draw', 'onSizeChanged', 'invalidate', 'invalidateChildInParent'):
        print(f"\n  -- {nm} {m.get_descriptor()} codelen={m.get_code() and m.get_code().get_length() or 0}")
        seen = set()
        for op, s in calls_of(m):
            line = f"     {op:16s} {s[:160]}"
            if line not in seen:
                seen.add(line); print(line)

# ---------- Q3: Lpz0; M0/L0/T0 ----------
print("\n=== Q3: Lpz0; methods M0/L0/T0 (layer drawContent family) ===")
_, c = find_class('Lpz0;')
if c:
    for m in c.get_methods():
        if m.get_name() in ('M0', 'L0', 'T0'):
            print(f"\n  -- M={m.get_name()} {m.get_descriptor()} codelen={m.get_code() and m.get_code().get_length() or 0}")
            seen = set()
            for op, s in calls_of(m):
                line = f"     {op:16s} {s[:160]}"
                if line not in seen:
                    seen.add(line); print(line)
else:
    print("  Lpz0; NOT FOUND")

# ---------- Q4: canvas holder / Canvas factory ----------
print("\n=== Q4: classes declaring Canvas-factory-ish statics (returns Ljt1;/Canvas iface) ===")
cnt = 0
for cname, (n, c) in cls.items():
    for m in c.get_methods():
        if m.get_descriptor().endswith(')Ljt1;') or m.get_descriptor().endswith(')Ljt2;'):
            print(f"  {cname}->{m.get_name()} {m.get_descriptor()}")
            cnt += 1
            if cnt > 20: break
    if cnt > 20: break
