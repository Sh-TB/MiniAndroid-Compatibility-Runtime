#!/usr/bin/env python3
# ============================================================================
# S43 probe #3 — dump the content-lambda class (Lrr0;) + interface (Lj90;)
# ----------------------------------------------------------------------------
# Probe #2 established (MainActivity.onCreate ground truth):
#   0188: new-instance Lrr0;  <- THE content lambda
#   018c: invoke-direct Lrr0;-><init>(LMainActivity; I)   (receiver, key)
#   0192: new-instance Lom;   <- wrapper (S41-r2: 'wrapper Lom;')
#   019c: invoke-direct Lom;-><init>(I Ljava/lang/Object; Z)
#   01ea/0202: Lho;->setContent(Lj90;)V   <- AbstractComposeView.setContent
#             with the Lom; wrapper — Lj90; = the composable-lambda interface
# Probe #1 showed ZERO (Object,Object)Object methods → R8 full-mode
# specialized the generic signatures → the interface method descriptor IS
# the ground truth to discover, not assume.
#
# This probe dumps:
#   A) Lj90; interface: which classes implement it + its method shape
#   B) Lrr0; class: interfaces it implements + every method + bytecode of
#      its invoke-shaped method (the one realFn(composer,1) must reach)
#   C) Lho; (AbstractComposeView): all methods, to anchor setContent chain
#   D) Lom; wrapper: methods (how the lambda is stored/invoked through it)
# All dumps fully annotated so the engine law can be derived mechanically.
# ============================================================================
import zipfile
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/home/z/my-project/corpus_cache/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]

classes, methods = {}, {}
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        name = c.get_name()
        if name not in classes:
            classes[name] = (dn, c)
        for m in c.get_methods():
            methods[(name, m.get_name(), m.get_descriptor())] = m

def disasm(m, maxn=400):
    out, idx, n = [], 0, 0
    code = m.get_code()
    if code is None:
        return out
    for ins in code.get_bc().get_instructions():
        if n >= maxn:
            out.append((idx, "…TRUNC", "")); break
        try:
            out.append((idx, ins.get_name(), ins.get_output()))
        except Exception:
            out.append((idx, "?", ""))
        idx += ins.get_length(); n += 1
    return out

def dump_class_info(cn):
    """Header info: superclass + interfaces list."""
    cd = classes.get(cn)
    if not cd:
        print(f"  [class {cn} NOT FOUND]"); return
    cls = cd[1]
    try:
        sup = cls.get_superclassname()
    except Exception:
        sup = '?'
    try:
        ifaces = list(cls.get_interfaces())
    except Exception:
        ifaces = []
    print(f"  class {cn}")
    print(f"    extends: {sup}")
    print(f"    implements: {ifaces}")

def dump_method(cn, mn, md, maxn=400):
    m = methods.get((cn, mn, md))
    if not m:
        print(f"  [method {cn}->{mn}{md} NOT FOUND]"); return
    print(f"  --- {cn}->{mn} {md} ---")
    for off, op, outp in disasm(m, maxn):
        print(f"    {off:04x}: {op} {outp}"[:190])

print("===== A) Lj90; interface shape =====")
dump_class_info('Lj90;')
cd = classes.get('Lj90;')
if cd:
    for m in cd[1].get_methods():
        print(f"    method: {m.get_name()} {m.get_descriptor()}  abstract={m.get_code() is None}")
    # who implements Lj90;? scan all classes' interface lists
    impls = []
    for cn, (dn, c) in classes.items():
        try:
            if 'Lj90;' in list(c.get_interfaces()):
                impls.append(cn)
        except Exception:
            pass
    print(f"    implementers ({len(impls)}): {impls[:12]}{' …' if len(impls)>12 else ''}")

print("\n===== B) Lrr0; content-lambda class =====")
dump_class_info('Lrr0;')
cd = classes.get('Lrr0;')
if cd:
    for m in cd[1].get_methods():
        print(f"    method: {m.get_name()} {m.get_descriptor()}  code={'Y' if m.get_code() else 'N'}")

print("\n===== C) Lho; (AbstractComposeView) methods =====")
dump_class_info('Lho;')
cd = classes.get('Lho;')
if cd:
    for m in cd[1].get_methods():
        print(f"    method: {m.get_name()} {m.get_descriptor()}")

print("\n===== D) Lom; wrapper methods =====")
dump_class_info('Lom;')
cd = classes.get('Lom;')
if cd:
    for m in cd[1].get_methods():
        print(f"    method: {m.get_name()} {m.get_descriptor()}")
