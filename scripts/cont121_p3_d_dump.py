#!/usr/bin/env python3
"""CONT-121 W-01: dump p3.d(I) — the RawMessageInfo builder — plus the
static fields it reads (info string / objects array provenance)."""
import os
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex

OUT = "run/c121"
dex_path = os.path.join(OUT, "classes_extracted.dex")
a, d, dx = AnalyzeDex(dex_path)
PB = "Lcom/google/android/gms/internal/play_billing/"

cls = d.get_class(PB + "p3;")
for m in cls.get_methods():
    if m.get_name() != "d":
        continue
    code = m.get_code()
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
    fn = os.path.join(OUT, "dis_p3_d.txt")
    with open(fn, "w") as f:
        f.write(f"# p3.d(I)Ljava/lang/Object;\n" + "\n".join(lines))
    print(f"p3.d: {len(lines)} insns -> {fn}")
    break

# also: which class holds the info string? check n2 (schema holder) static fields
n2c = d.get_class(PB + "n2;")
print("\n=== n2 static fields ===")
for f in n2c.get_fields():
    print(f"  {f.get_name()} : {f.get_descriptor()}  {hex(f.get_access_flags())}")

# v1 (GeneratedMessageLite shade) — where is messageInfo cached? and e1
for name in ["v1", "e1", "o3"]:
    c = d.get_class(PB + name + ";")
    print(f"\n=== {name} fields ===")
    for f in c.get_fields():
        print(f"  {f.get_name()} : {f.get_descriptor()}")
