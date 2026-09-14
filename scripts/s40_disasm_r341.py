#!/usr/bin/env python3
"""S40 FRONT-A: disassemble Lv;.n (ISE 'Could not find an Application in the
given context') and its caller Lt3;.q catch block from dooz23 APK."""
import sys, logging
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

APK_DEX = None
import zipfile, tempfile, os
apk = "/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk"
tmp = tempfile.mkdtemp()
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if n.startswith("classes") and n.endswith(".dex"):
            z.extract(n, tmp)
            print(f"extracted {n}")

targets = [("Lv;", "n"), ("Lt3;", "q")]
for fn in sorted(os.listdir(tmp)):
    path = os.path.join(tmp, fn)
    try:
        a, d, dx = AnalyzeDex(path)
    except Exception as e:
        print(f"skip {fn}: {e}"); continue
    for m in dx.get_methods():
        em = m.get_method()
        if em is None:
            continue
        cls = em.get_class_name()
        name = em.get_name()
        if (cls, name) in targets:
            print(f"\n===== {cls}->{name} {em.get_descriptor()} =====")
            code = em.get_code()
            if code is None:
                print("  <abstract/native>"); continue
            bc = code.get_bc()
            idx = 0
            for ins in bc.get_instructions():
                op = ins.get_name()
                out = f"  {idx:4d}: {op} {ins.get_output()}"
                print(out)
                idx += ins.get_length()
    # also find who references the ISE string
    for s in d.get_strings():
        sv = s.get_value()
        if "Could not find an Application" in sv:
            print(f"\n[STRING] in {fn}: {sv!r}")
