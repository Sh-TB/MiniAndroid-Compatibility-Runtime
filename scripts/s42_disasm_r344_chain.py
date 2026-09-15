#!/usr/bin/env python3
"""S42 Attack-1 (R-NEW-344 frontier): disassemble the deferred-compose-request
chain from dooz_23 DEX ground truth.

S41-r2 established:
  Lho;.setContent  -> content lambda PERSISTED (obj#886 into Lc41; obj#894 .c)
  Lr;.g            -> ensureCompositionCreated: builds holder Lx62;(view,owner,wrapper Lom;)
  La72;.a          -> creates AndroidComposeView Lt4; + addView, returns holder
  Lx62;.e          -> ON_CREATE handler -> Lx62;.f -> builds Ls7;(flag=8,view,wrapper)
  Lt4;.setOnReadyForComposition(Ls7;)  <- the DEFERRED compose request
  Ls7;.i           -> deferred invoke: Looper.myLooper() vs view.getHandler().getLooper()
                      identity check -> View.post(Lk5;) OR inline compose

S42 questions this script answers from pure bytecode:
  Q1: What is Ls7; exactly (fields, methods, super)?
  Q2: Full bytecode of Ls7;.i — every instruction, so we know BOTH branches
      and any extra guards (isAttachedToWindow / isShown / owner null ...).
  Q3: Who calls Lt4;.setOnReadyForComposition and who reads the stored
      request (field xref) — i.e., is the deferred invoke ever triggered?
  Q4: Full bytecode of Lk5; (the posted runnable) — what does its run() do?
  Q5: Lt4; methods touching onReadyForComposition / composition start.
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

APK = '/home/z/my-project/corpus_cache/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]

classes = {}   # name -> (dex, class)
methods = {}   # (cls, meth, desc) -> method obj  for xref scans
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        name = c.get_name()
        if name not in classes:
            classes[name] = (dn, c)
        for m in c.get_methods():
            methods[(name, m.get_name(), m.get_descriptor())] = m

def dump_bytecode(cls, meth, desc):
    key = (cls, meth, desc)
    if key not in methods:
        print(f"  (no method {cls}.{meth}{desc})")
        return
    m = methods[key]
    code = m.get_code()
    if code is None:
        print("  (abstract/native)")
        return
    idx = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        out = ins.get_output()
        print(f"    {idx:6d}: {op:28s} {out}")
        idx += ins.get_length()

# ---------- Q1/Q2: Ls7; full ----------
for t in sys.argv[1:] or ['Ls7;', 'Lk5;']:
    if t not in classes:
        print(f"### {t}: NOT FOUND"); continue
    dn, c = classes[t]
    print(f"\n### {t} (in {dn}) super={c.get_superclassname()}")
    ifaces = c.get_interfaces()
    if ifaces: print(f"    interfaces={ifaces}")
    for f in c.get_fields():
        print(f"    FIELD {f.get_name()} {f.get_descriptor()}")
    for m in c.get_methods():
        print(f"    METHOD {m.get_name()} {m.get_descriptor()} access={m.get_access_flags_string()}")

# ---------- Q2b: Ls7;.i full bytecode ----------
print("\n### BYTECODE Ls7;.i (deferred compose invocation)")
dump_bytecode('Ls7;', 'i', '()V')
print("\n### BYTECODE Lk5;.run (posted runnable)")
for (cn, mn, cd) in list(methods):
    if cn == 'Lk5;' and mn == 'run':
        dump_bytecode(cn, mn, cd)

# ---------- Q3: xref — who references Ls7; or setOnReadyForComposition ----------
print("\n### XREF: methods that reference setOnReadyForComposition / Ls7; / Lk5;")
needle_ops = ('invoke-virtual', 'invoke-direct', 'invoke-static',
              'invoke-super', 'invoke-interface', 'invoke-virtual/range',
              'invoke-direct/range', 'new-instance', 'sput-object',
              'sget-object', 'iput-object', 'iget-object', 'check-cast')
for (cn, mn, cd), m in methods.items():
    code = m.get_code()
    if code is None: continue
    hits = []
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        if op in needle_ops:
            out = ins.get_output()
            if ('Ls7;' in out and cn != 'Ls7;') or \
               ('setOnReadyForComposition' in out) or \
               ('Lk5;' in out and cn != 'Lk5;'):
                hits.append(f"{op} {out}")
    if hits:
        print(f"  {cn}.{mn}{cd}:")
        for h in hits[:12]:
            print(f"      {h}")
