#!/usr/bin/env python3
"""S42 Attack-1 round-2: map the FULL onReadyForComposition contract.

Round-1 established:
  Ls7; : implements Lf90;  — the suspend callback stored by Lt4;.setOnReadyForComposition
  Only producer: Lx62;.f(Lj90;)V

Round-2 questions:
  R1: Lf90; interface shape (the callback contract).
  R2: Lx62; full class map + bytecode of .e/.f (the ON_CREATE handler chain).
  R3: Lt4; (AndroidComposeView) fields + all methods; find the field that
      stores the Lf90; callback and every method reading/invoking it.
  R4: Full bytecode of Ls7;.i(Ljava/lang/Object;)Ljava/lang/Object; — the
      deferred invoke with BOTH branches.
  R5: Who calls Lx62;.f / who calls Lx62;.e (xref).
"""
import zipfile, sys
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'
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

def dump_bytecode(cls, meth, desc, maxn=400):
    m = methods.get((cls, meth, desc))
    if m is None:
        print(f"  (no {cls}.{meth}{desc})"); return
    code = m.get_code()
    if code is None:
        print("  (abstract/native)"); return
    idx = 0; n = 0
    for ins in code.get_bc().get_instructions():
        if n >= maxn:
            print(f"    ... truncated at {maxn} ins"); break
        print(f"    {idx:6d}: {ins.get_name():28s} {ins.get_output()}")
        idx += ins.get_length(); n += 1

which = sys.argv[1] if len(sys.argv) > 1 else 'all'

# R1
if which in ('all', 'f90'):
    dn, c = classes['Lf90;']
    print(f"### Lf90; super={c.get_superclassname()} ifaces={c.get_interfaces()}")
    for f in c.get_fields(): print(f"  FIELD {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods(): print(f"  METHOD {m.get_name()} {m.get_descriptor()} {m.get_access_flags_string()}")

# R2
if which in ('all', 'x62'):
    dn, c = classes['Lx62;']
    print(f"\n### Lx62; super={c.get_superclassname()} ifaces={c.get_interfaces()}")
    for f in c.get_fields(): print(f"  FIELD {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods(): print(f"  METHOD {m.get_name()} {m.get_descriptor()} {m.get_access_flags_string()}")
    for mn, cd in [('.e', '()V'), ('.f', '(Lj90;)V')]:
        # find by prefix match on name
        for (cn, mname, mdesc) in list(methods):
            if cn == 'Lx62;' and mname == mn[1:]:
                print(f"\n### BYTECODE Lx62;.{mname}{mdesc}")
                dump_bytecode(cn, mname, mdesc)

# R3
if which in ('all', 't4'):
    dn, c = classes['Lt4;']
    print(f"\n### Lt4; super={c.get_superclassname()}")
    ifaces = c.get_interfaces()
    print(f"  ifaces={ifaces}")
    for f in c.get_fields():
        if 'f90' in f.get_descriptor() or 'Ls7;' in f.get_descriptor():
            print(f"  >>> FIELD {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods():
        print(f"  METHOD {m.get_name()} {m.get_descriptor()}")

# R4
if which in ('all', 's7'):
    print("\n### BYTECODE Ls7;.i(Ljava/lang/Object;)Ljava/lang/Object;")
    dump_bytecode('Ls7;', 'i', '(Ljava/lang/Object;)Ljava/lang/Object;', maxn=600)

# R5: xref
if which in ('all', 'xref'):
    print("\n### XREF: who invokes Lx62;.f / Lx62;.e / invokes Lf90;.i")
    for (cn, mn, cd), m in methods.items():
        code = m.get_code()
        if code is None: continue
        hits = []
        for ins in code.get_bc().get_instructions():
            op = ins.get_name(); out = ins.get_output()
            if (op.startswith('invoke') and ('Lx62;->f(' in out or 'Lx62;->e(' in out)) or \
               (op.startswith('invoke') and 'Lf90;->i(' in out):
                hits.append(f"{op} {out}")
        if hits:
            print(f"  {cn}.{mn}{cd}:")
            for h in hits[:10]: print(f"      {h}")
