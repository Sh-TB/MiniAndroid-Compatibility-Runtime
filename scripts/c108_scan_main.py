#!/usr/bin/env python3
"""CONT-108 / F-NEW-451 decode: MainActivity getDrawable(below_shadow) call-site.

Pre-107: MainActivity.getDrawable(0x7f08007f below_shadow) IS reached after
SlidingUpPanelLayout.<init> during activity_main inflation.
Post-107 (AOSP-true umanoPanelHeight 108px): the call is NOT reached; instead a
`get` dispatch happens. This scan disassembles every MainActivity method that
invokes getDrawable / SlidingUpPanelLayout usage and prints the CFG context so
the branch that gates the call can be identified.
Output: run/c108/oc_mainactivity_scan.txt
"""
import sys
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/opencalculator_53.apk"
OUT = "run/c108/oc_mainactivity_scan.txt"
L = []

a = APK(APK_PATH)
dexes = [DEX(d) for d in a.get_all_dex()]

MAIN = "Lcom/darkempire78/opencalculator/activities/MainActivity;"

# 1) locate every method in MainActivity (and parents) that references
#    getDrawable or SlidingUpPanelLayout
for di, d in enumerate(dexes):
    for c in d.get_classes():
        if c.get_name() != MAIN:
            continue
        L.append(f"[main] found in dex#{di}")
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            names = set()
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                if "invoke" in op:
                    try:
                        operands = ins.get_operands()
                        meth = operands[-1][2]
                        if isinstance(meth, str):
                            names.add(meth)
                    except Exception:
                        pass
            hit = [n for n in names if "getDrawable" in n or "SlidingUpPanelLayout" in n or "below_shadow" in n]
            if hit:
                L.append(f"\n=== {m.get_name()} {m.get_descriptor()} hits={hit}")

# 2) dump onCreate fully (and any method calling getDrawable) with instructions
def dump_method(c, m, out):
    out.append(f"\n#### {c.get_name()}->{m.get_name()}{m.get_descriptor()}")
    code = m.get_code()
    if code is None:
        out.append("  <no code>")
        return
    idx = 0
    for pc_i, ins in enumerate(code.get_bc().get_instructions()):
        try:
            op = ins.get_name()
            operands = ins.get_operands()
            ops = []
            for o in operands:
                if o[0] == 0:  # literal
                    ops.append(str(o[1]))
                elif isinstance(o[2], str):
                    ops.append(o[2])
                else:
                    ops.append(f"v{o[1]}")
            out.append(f"  {idx:5d} {op:26s} {', '.join(ops)[:120]}")
        except Exception as e:
            out.append(f"  {idx:5d} <err {e}>")
        idx += ins.get_length()

for di, d in enumerate(dexes):
    for c in d.get_classes():
        if c.get_name() != MAIN:
            continue
        for m in c.get_methods():
            if m.get_name() in ("onCreate", "onCreateView", "init") or "onCreate" in m.get_name():
                dump_method(c, m, L)

open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT}: {len(L)} lines")
