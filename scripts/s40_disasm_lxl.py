#!/usr/bin/env python3
"""S40: disassemble Lqi0;.S (Lxl throw site), find callers of Lqi0;.S and
the Le;.q / Lne;.g frames in the dooz23 R341 frontier chain."""
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
a, d, dx = AnalyzeDex(os.path.join(tmp, "classes.dex"))

def dump(cls_name, meth_name, limit=90):
    for m in dx.get_methods():
        em = m.get_method()
        if em is None or not hasattr(em, "get_code"): continue
        if em.get_class_name() == cls_name and em.get_name() == meth_name:
            code = em.get_code()
            if code is None:
                print(f"===== {cls_name}->{meth_name} <no code> ====="); return
            print(f"===== {cls_name}->{meth_name} {em.get_descriptor()} =====")
            idx = 0
            for i, ins in enumerate(code.get_bc().get_instructions()):
                print(f"  {idx:4d}: {ins.get_name()} {ins.get_output()}")
                idx += ins.get_length()
                if i > limit: print("  ...truncated"); break
            return
    print(f"===== {cls_name}->{meth_name} NOT FOUND =====")

dump("Lqi0;", "S")
dump("Le;", "q", 60)

# class info
for n in ("Lqi0;", "Le;", "Lne;", "Lxl;", "Lhf;"):
    for c in d.get_classes():
        if c.get_name() == n:
            print(f"class {n} super={c.get_superclassname()} ifs={list(c.get_interfaces())}")

# find callers of Lqi0;.S via analysis
print("\n=== callers of Lqi0;->S ===")
for m in dx.get_methods():
    em = m.get_method()
    if em is None or not hasattr(em, "get_code"): continue
    code = em.get_code()
    if code is None: continue
    try:
        for ins in code.get_bc().get_instructions():
            if "invoke" in ins.get_name() and "Lqi0;->S" in ins.get_output():
                print(f"  caller: {em.get_class_name()}->{em.get_name()} {em.get_descriptor()}")
                break
    except Exception:
        pass
