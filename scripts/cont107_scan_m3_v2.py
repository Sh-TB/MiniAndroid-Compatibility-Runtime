#!/usr/bin/env python3
"""CONT-107 / F-NEW-448 decode v2: the Ll/m3; class + full Toolbar.onMeasure.

v1 finding: Toolbar.onMeasure opens with `sget-boolean v1, Ll/m3;->a :Z` and
v1 is immediately overwritten by getLayoutDirection's move-result — the sget
is a CLASS-INIT TRIGGER. The height-0 face must therefore live in (a) m3's
<clinit> never running (its other statics stay default) or (b) another static
read deeper in onMeasure.

Dumps: Ll/m3; field table, <clinit> bytecode, every writer of a:Z, every
static read inside Toolbar.onMeasure (class->field), and the full onMeasure
instruction stream.
Output: run/c107/m3_scan2.txt
"""
import sys
from androguard.core.dex import DEX
from androguard.core.apk import APK

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/chess_jwtc_298.apk"
OUT = "run/c107/m3_scan2.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

m3 = None
toolbar = None
for di, d in enumerate(dexes):
    for c in d.get_classes():
        if c.get_name() == "Ll/m3;":
            m3 = c
        elif c.get_name() == "Landroidx/appcompat/widget/Toolbar;":
            toolbar = c

if m3 is None:
    L.append("[m3] class Ll/m3; NOT FOUND")
else:
    L.append(f"[m3] fields:")
    for f in m3.get_fields():
        L.append(f"  {f.get_name()} : {f.get_descriptor()} access=0x{int(f.get_access_flags()):x}")
    for m in m3.get_methods():
        L.append(f"[m3] method {m.get_name()} {m.get_descriptor()} access=0x{int(m.get_access_flags()):x}")
        code = m.get_code()
        if code is None:
            continue
        for i in code.get_bc().get_instructions():
            try:
                L.append(f"  {i.get_name():16s} {i.get_output()}")
            except Exception:
                L.append(f"  {i.get_name():16s} <no-output>")

if toolbar is not None:
    for m in toolbar.get_methods():
        if m.get_name() != "onMeasure":
            continue
        L.append(f"[onMeasure] {m.get_descriptor()}")
        code = m.get_code()
        if code is None:
            continue
        idx = 0
        static_reads = []
        for i in code.get_bc().get_instructions():
            op = i.get_name()
            try:
                out = i.get_output()
            except Exception:
                out = "<no-output>"
            if op.startswith("sget"):
                static_reads.append(out)
            L.append(f"  {idx:4d} {op:18s} {out}")
            idx += 1
        L.append("[onMeasure] STATIC READS:")
        for s in static_reads:
            L.append(f"  {s}")

# writers of Ll/m3;->a:Z
if m3 is not None:
    writers = []
    key = "Ll/m3;->a:Z"
    for di, d in enumerate(dexes):
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if code is None:
                    continue
                for i in code.get_bc().get_instructions():
                    if i.get_name().startswith("sput"):
                        try:
                            if i.get_string() == key:
                                writers.append(f"{c.get_name()}->{m.get_name()}{m.get_descriptor()}")
                        except Exception:
                            pass
    L.append(f"[m3] a:Z WRITERS: {writers}")

with open(OUT, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {OUT}: {len(L)} lines")
for line in L[:28]:
    print(line)
