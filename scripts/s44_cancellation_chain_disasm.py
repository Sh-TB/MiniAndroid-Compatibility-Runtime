#!/usr/bin/env python3
"""S44 Attack-2 (post-R-NEW-353 frontier): identify the cancellation chain.

After R-NEW-353 the protobuf schema builds, composition machinery runs, but:
  - Choreographer cb=1073 posted (pending=1) then REMOVED twice, never run
  - AndroidComposeView Lt4; = 0 children, 0x0, invisible
  - content lambda Lrr0; never invoked
  - `La;` exceptions unwind Lzs;.m / Lte1;.f / Lse1;.s from thrower La7;.m

This script answers:
  Q1: What class is `La;` (super, fields) — CancellationException?
  Q2: What does the thrower La7;.m look like (which throw at pc 32)?
  Q3: What are Lzs;.m / Lte1;.f doing (te1 = preferences serializer?)
  Q4: Who calls removeFrameCallback (Lh9; relationship)?
"""
import zipfile, logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

WANT = {'La;', 'La7;', 'Lzs;', 'Lte1;', 'Lh9;', 'Lse1;'}
classes = {c.get_name(): c for c in d.get_classes() if c.get_name() in WANT}
methods = {}
for c in d.get_classes():
    for m in c.get_methods():
        methods[(c.get_name(), m.get_name(), m.get_descriptor())] = m

for cn in ['La;', 'La7;', 'Lzs;', 'Lte1;', 'Lh9;', 'Lse1;']:
    c = classes.get(cn)
    if not c:
        print(f"=== {cn}: NOT FOUND ===")
        continue
    print(f"=== {cn} extends {c.get_superclassname()} ===")
    for f in c.get_fields():
        print(f"  field {f.get_name()} : {f.get_descriptor()}")
    for m in c.get_methods():
        print(f"  method {m.get_name()}{m.get_descriptor()}")

# dump the exact methods on the unwind chain
for (cn, mn) in [('La7;', 'm'), ('Lzs;', 'm'), ('Lte1;', 'f'), ('Lse1;', 's'), ('Lh9;', 'doFrame')]:
    found = False
    for (k, m) in methods.items():
        if k[0] == cn and k[1] == mn:
            code = m.get_code()
            print(f"\n=== {cn};.{mn}{k[2]} ===")
            if code is None:
                print("  (abstract)")
                continue
            pc = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                marker = ' <== THROW' if 'throw' in op else ''
                if len(insns_filter := []) == 0:  # noqa
                    pass
                print(f"  {pc:5d} {op:26s} {out}{marker}")
                pc += ins.get_length()
            found = True
            break
    if not found:
        print(f"\n=== {cn};.{mn}: no such method ===")
