#!/usr/bin/env python3
"""W15 recon #3: itsfrz full NavHostFragment method list + nav graph XML dump + where NavHostFragment is referenced."""
import json, logging, zipfile
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk"
a = APK(APK_PATH)
z = zipfile.ZipFile(APK_PATH)

# 1. all NavHostFragment methods
dexes = [DEX(b) for b in a.get_all_dex()]
def disasm(m, limit=400):
    out = []
    if not m.get_code(): return out
    for ins in m.get_code().get_bc().get_instructions():
        out.append(ins.get_name() + " " + str(ins.get_output())[:100])
        if len(out) >= limit: break
    return out

for d in dexes:
    for c in d.get_classes():
        if c.get_name() == "Landroidx/navigation/fragment/NavHostFragment;":
            print("=== NavHostFragment methods ===")
            for m in c.get_methods():
                print(f"  {m.get_name()} {m.get_descriptor()} access={m.get_access_flags_string()}")
            # dump onInflate and onCreate fully
            for m in c.get_methods():
                if m.get_name() in ("onInflate", "onCreate", "onCreateView", "onAttach"):
                    print(f"\n### FULL {m.get_name()}{m.get_descriptor()}")
                    for l in disasm(m): print("   ", l)

# 2. dump nav graph v9.xml (binary AXML)
print("\n=== res/v9.xml (nav graph, first 800 bytes hex-ish) ===")
data = z.read("res/v9.xml")
open("/home/z/my-project/macr/evidence/w15/itsfrz_navgraph_v9.axml", "wb").write(data)
print("size", len(data))

# 3. which files reference NavHostFragment string
print("\n=== files containing 'NavHostFragment' bytes ===")
for n in z.namelist():
    try:
        if b"NavHostFragment" in z.read(n):
            print("  ", n)
    except Exception:
        pass

# 4. main activity class + its layout
for d in dexes:
    for c in d.get_classes():
        cn = str(c.get_name())
        if "itsfrz" in cn and ("MainActivity" in cn or "Activity" in cn.split("/")[-1]):
            print("\n=== APP ACTIVITY ===", cn, "super:", c.get_superclassname())
            for m in c.get_methods():
                if m.get_name() in ("<init>", "onCreate"):
                    print(f"  ### {m.get_name()}{m.get_descriptor()}")
                    for l in disasm(m, 150): print("     ", l)
