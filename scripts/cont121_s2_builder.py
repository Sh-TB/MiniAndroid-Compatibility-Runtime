#!/usr/bin/env python3
"""CONT-121 W-01: find who constructs s2 (RawMessageInfo) — xref of
s2;-><init>(e1,String,[Ljava/lang/Object;)V and the Object[] source."""
import os
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

OUT = "run/c121"
dex_path = os.path.join(OUT, "classes_extracted.dex")
a, d, dx = AnalyzeDex(dex_path)

PB = "Lcom/google/android/gms/internal/play_billing/"

# 1. xref: who calls s2.<init>?
s2cls = d.get_class(PB + "s2;")
init = None
for m in s2cls.get_methods():
    if m.get_name() == "<init>":
        init = m
        break
callers = set()
if init:
    mai = dx.get_method(init)
    try:
        for cls_obj, meth_obj, _ in mai.get_xref_from():
            callers.add(f"{meth_obj.get_class_name()}.{meth_obj.get_name()}{meth_obj.get_descriptor()}")
    except Exception:
        # androguard 4.x: xref tuples are (classobj, methodobj)
        for item in mai.get_xref_from():
            meth_obj = item[1] if isinstance(item, tuple) else item
            try:
                callers.add(f"{meth_obj.get_class_name()}.{meth_obj.get_name()}{meth_obj.get_descriptor()}")
            except Exception:
                callers.add(str(item))
print("=== s2.<init> xref-from ===")
for c in sorted(callers):
    print("  ", c)

# 2. who READS/WWRITES s2.c or s2 fields; who calls s2.a()?
print("\n=== s2 method/field xrefs ===")
for m in s2cls.get_methods():
    if m.get_name() == "<init>":
        continue
    for _, call, _ in dx.get_xref_from(m):
        print(f"  s2.{m.get_name()} -> {call}")

# 3. dump the caller method(s) that construct s2 — find Object[] creation there
import re
for c in sorted(callers):
    mm = re.match(r"(\S+)\s+(\S+)\.(\S+)\(", c)
    # androguard xref string format varies; robust: parse class+method tokens
    mre = re.search(r"(L[\w/$]+;)\.?\s*(\S+)?\(", c)
    if not mre:
        continue
    cls_desc = mre.group(1)
    cls = d.get_class(cls_desc)
    if cls is None:
        print(f"caller class {cls_desc} not in classes.dex (multi-dex)")
        continue
    print(f"\n=== caller class {cls_desc} ===")
    print("superclass:", cls.get_superclassname())
    for m in cls.get_methods():
        code = m.get_code()
        if not code:
            continue
        off = 0
        na = []
        ao = []
        invokes_s2 = []
        sgets = []
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            try:
                outp = ins.get_output()
            except Exception:
                outp = ""
            if op.startswith("new-array") and "[Ljava/lang/Object;" in outp:
                na.append((hex(off), outp))
            if op.startswith("aput-object"):
                ao.append((hex(off), outp))
            if "s2;-><init>" in outp:
                invokes_s2.append((hex(off), op, outp))
            if op.startswith(("sget", "sput")) and cls_desc.split("/")[-1] in outp:
                sgets.append((hex(off), op, outp))
            off += ins.get_length()
        if invokes_s2:
            print(f"  METHOD {m.get_name()} {m.get_descriptor()}: insns={off//2}")
            print(f"    new-array[Object]={na[:8]}")
            print(f"    aput-object count={len(ao)}")
            print(f"    s2-init calls={invokes_s2}")
            fn = os.path.join(OUT, f"dis_s2builder_{cls_desc.split('/')[-1]}_{m.get_name()}.txt")
            lines = []
            off = 0
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                try:
                    txt = f"{off:04x}: {op} {ins.get_output()}"
                except Exception:
                    txt = f"{off:04x}: {op} <err>"
                off += ins.get_length()
                lines.append(txt)
            with open(fn, "w") as f:
                f.write(f"# {cls_desc}.{m.get_name()}\n" + "\n".join(lines))
            print(f"    -> dumped {fn}")
