#!/usr/bin/env python3
"""S40 FRONT-A step 2: find which method holds the ISE string and disassemble
the whole walk-to-Application chain (Lk2;.b, Lu32; impls, MainActivity.l)."""
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex
import zipfile, tempfile, os

apk = "/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk"
tmp = tempfile.mkdtemp()
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if n.startswith("classes") and n.endswith(".dex"):
            z.extract(n, tmp)

path = os.path.join(tmp, "classes.dex")
a, d, dx = AnalyzeDex(path)

NEEDLE = "Could not find an Application"
holder = None
# brute-force: scan every method's bytecode for const-string with needle
for m in dx.get_methods():
    em = m.get_method()
    if em is None or not hasattr(em, 'get_code'): continue
    code = em.get_code()
    if code is None: continue
    try:
        for ins in code.get_bc().get_instructions():
            if ins.get_name().startswith("const-string") and NEEDLE in ins.get_output():
                print(f"[STRING-USER] {em.get_class_name()}->{em.get_name()} {em.get_descriptor()}")
                holder = em
                break
    except Exception:
        pass

def dump(cls_name, meth_name, maxins=400):
    for m in dx.get_methods():
        em = m.get_method()
        if em is None: continue
        if em.get_class_name() == cls_name and em.get_name() == meth_name:
            code = em.get_code()
            if code is None:
                print(f"===== {cls_name}->{meth_name} <no code> ====="); return
            print(f"===== {cls_name}->{meth_name} {em.get_descriptor()} =====")
            idx = 0
            for i, ins in enumerate(code.get_bc().get_instructions()):
                print(f"  {idx:4d}: {ins.get_name()} {ins.get_output()}")
                idx += ins.get_length()
                if i > maxins: print("  ...truncated"); break
            return
    print(f"===== {cls_name}->{meth_name} NOT FOUND =====")

dump("Lk2;", "b")
dump("Lio/github/yamin8000/dooz/ui/MainActivity;", "l")
