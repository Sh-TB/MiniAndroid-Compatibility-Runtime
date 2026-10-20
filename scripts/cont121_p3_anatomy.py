#!/usr/bin/env python3
"""CONT-121 W-01 follow-up: p3 class anatomy + find the Object[11] builder.
Dumps p3 superclass, static fields, s2 class, and scans play_billing
<clinit>s for new-array of Object arrays with size 11 filled with strings.
"""
import os, json
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

OUT = "run/c121"
dex_path = os.path.join(OUT, "classes_extracted.dex")
a, d, dx = AnalyzeDex(dex_path)

PB = "Lcom/google/android/gms/internal/play_billing/"

# 1. p3 anatomy
p3 = d.get_class(PB + "p3;")
print("=== p3 anatomy ===")
print("superclass:", p3.get_superclassname())
print("interfaces:", [i.get_name() for i in (p3.get_interfaces() or [])])
for f in p3.get_fields():
    print(f"  field: {f.get_name()} : {f.get_descriptor()}  access={hex(f.get_access_flags())}")
print("methods:", [(m.get_name(), m.get_descriptor()) for m in p3.get_methods()])

# 2. s2 anatomy (RawMessageInfo)
s2 = d.get_class(PB + "s2;")
print("\n=== s2 anatomy ===")
print("superclass:", s2.get_superclassname() if s2 else None)
if s2:
    for f in s2.get_fields():
        print(f"  field: {f.get_name()} : {f.get_descriptor()}")
    for m in s2.get_methods():
        print(f"  method: {m.get_name()} {m.get_descriptor()}")

# 3. p3 superclass <clinit> — the likely Object[] builder
sup = p3.get_superclassname()
print("\n=== superclass", sup, "<clinit> ===")
if sup:
    sc = d.get_class(sup)
    if sc:
        print("superclass's superclass:", sc.get_superclassname())
        for m in sc.get_methods():
            if m.get_name() == "<clinit>":
                code = m.get_code()
                if code:
                    lines = []
                    off = 0
                    for ins in code.get_bc().get_instructions():
                        op = ins.get_name()
                        try:
                            txt = f"{off:04x}: {op} {ins.get_output()}"
                        except Exception as e:
                            txt = f"{off:04x}: {op} <err>"
                        off += ins.get_length()
                        lines.append(txt)
                    fn = os.path.join(OUT, "dis_super_clinit.txt")
                    with open(fn, "w") as f:
                        f.write(f"# {sup}.<clinit>\n" + "\n".join(lines))
                    na = sum(1 for l in lines if l.split(": ",1)[1].startswith("new-array"))
                    ao = sum(1 for l in lines if ": aput-object" in l)
                    fnac = sum(1 for l in lines if "filled-new-array" in l)
                    print(f"  {len(lines)} insns -> {fn}  new-array={na} aput-object={ao} filled-new-array={fnac}")

# 4. Scan ALL play_billing <clinit>s for Object[] new-array with 11 elements
print("\n=== play_billing <clinit> Object-array scan ===")
for c in d.get_classes():
    if not c.get_name().startswith(PB):
        continue
    for m in c.get_methods():
        if m.get_name() != "<clinit>":
            continue
        code = m.get_code()
        if not code:
            continue
        hits = []
        off = 0
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            try:
                outp = ins.get_output()
            except Exception:
                outp = ""
            if op.startswith("new-array") and "[Ljava/lang/Object;" in outp:
                hits.append((hex(off), op, outp))
            off += ins.get_length()
        if hits:
            print(f"  {c.get_name()}.<clinit>: {hits}")
