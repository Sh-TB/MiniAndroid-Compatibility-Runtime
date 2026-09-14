#!/usr/bin/env python3
"""S40: disassemble dooz23 App class + hierarchy to design the Application law."""
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

# 1) hierarchy of App
TARGET = "Lio/github/yamin8000/dooz/ui/App;"
for c in d.get_classes():
    if c.get_name() == TARGET:
        print(f"class {c.get_name()}  super={c.get_superclassname()}")
        for f in c.get_fields():
            print(f"  field {f.get_name()} {f.get_descriptor()}")
        for m in c.get_methods():
            print(f"  method {m.get_name()} {m.get_descriptor()}")

# 2) dump App methods that matter
def dump(cls_name, meth_name):
    for m in dx.get_methods():
        em = m.get_method()
        if em is None or not hasattr(em, "get_code"): continue
        if em.get_class_name() == cls_name and em.get_name() == meth_name:
            code = em.get_code()
            if code is None:
                print(f"===== {cls_name}->{meth_name} <no code> ====="); return
            print(f"===== {cls_name}->{meth_name} {em.get_descriptor()} =====")
            idx = 0
            for ins in code.get_bc().get_instructions():
                print(f"  {idx:4d}: {ins.get_name()} {ins.get_output()}")
                idx += ins.get_length()
            return
    print(f"===== {cls_name}->{meth_name} NOT FOUND =====")

dump(TARGET, "onCreate")
dump(TARGET, "<init>")
# Ll2; — the EntryPoint interface the Application gets cast to
for c in d.get_classes():
    if c.get_name() == "Ll2;":
        print(f"class {c.get_name()} super={c.get_superclassname()}")
        for m in c.get_methods()[:12]:
            print(f"  method {m.get_name()} {m.get_descriptor()}")
