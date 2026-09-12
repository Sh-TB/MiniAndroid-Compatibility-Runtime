#!/usr/bin/env python3
"""Scan a classes.dex for which framework classes/methods are invoked —
used to answer 'what scheduling mechanism does this app really use?'."""
import re
import sys
import zipfile

from androguard.core.bytecodes.dvm import DalvikVMFormat

apk = sys.argv[1]
z = zipfile.ZipFile(apk)
f = DalvikVMFormat(z.read("classes.dex"))

cls_count = {}
meth_hits = {}
for m in f.get_methods():
    cn = m.get_class_name()
    mn = m.get_name()
    code = m.get_code()
    if code is None:
        continue
    try:
        for ins in m.get_instructions():
            if not ins.get_name().startswith("invoke"):
                continue
            out = ins.get_output()
            mm = re.search(r"(L[\w/$-]+;)->([\w<>$]+)", out)
            if not mm:
                continue
            c, name = mm.group(1), mm.group(2)
            cls_count[c] = cls_count.get(c, 0) + 1
            key = (c, name)
            meth_hits.setdefault(key, []).append(f"{cn}.{mn}")
    except Exception:
        continue

print("distinct invoked classes:", len(cls_count))
print()
for c, n in sorted(cls_count.items(), key=lambda x: -x[1])[:30]:
    print(f"{n:5d}  {c}")
print()
print("--- scheduling-relevant call sites ---")
for (c, name), sites in sorted(meth_hits.items()):
    if any(s in c for s in ("Thread", "Timer", "Coroutine", "Handler", "Looper",
                            "Executor", "Sleep", "Latch", "Atomic", "Future")):
        print(f"{c}-> {name}:  {sorted(set(sites))[:4]}")
