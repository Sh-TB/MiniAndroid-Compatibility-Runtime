#!/usr/bin/env python3
"""W15 recon #5: itsfrz death-site decode — LU1/r;.<init> (Fragment ctor pc=0x45) + LC4/u;.s + NavHostFragment lazy NavController."""
import logging
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk"
a = APK(APK_PATH)
dexes = [DEX(b) for b in a.get_all_dex()]

def disasm(m, limit=600):
    out = []
    if not m.get_code(): return out
    for ins in m.get_code().get_bc().get_instructions():
        out.append(f"pc={ins.get_length():x} " + ins.get_name() + " " + str(ins.get_output())[:110])
        if len(out) >= limit: break
    return out

# track pc offsets properly
def disasm_pc(m, limit=600):
    out = []
    if not m.get_code(): return out
    pc = 0
    for ins in m.get_code().get_bc().get_instructions():
        out.append(f"pc=0x{pc:03x} " + ins.get_name() + " " + str(ins.get_output())[:110])
        pc += ins.get_length()
        if len(out) >= limit: break
    return out

TARGETS = {"LU1/r;": ("<init>",), "LC4/u;": ("s", "<init>", "inflate")}

for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        if cn in TARGETS:
            print(f"\n===== {cn} (super={c.get_superclassname()}) =====")
            for m in c.get_methods():
                if m.get_name() in TARGETS[cn]:
                    print(f"### {m.get_name()} {m.get_descriptor()}")
                    for l in disasm_pc(m, 120): print("   ", l)

# NavHostFragment <init> + clinit (lazy NavController creation) + who reads a0
for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        if cn == "Landroidx/navigation/fragment/NavHostFragment;":
            for m in c.get_methods():
                if m.get_name() in ("<init>", "<clinit>"):
                    print(f"\n### NavHostFragment {m.get_name()} {m.get_descriptor()}")
                    for l in disasm_pc(m, 150): print("   ", l)
