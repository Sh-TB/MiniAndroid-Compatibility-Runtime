#!/usr/bin/env python3
"""W15 recon #4: itsfrz NavHostFragment method bodies (y=onInflate, s=onCreate, O=getNavController, t=onCreateView)."""
import logging
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk"
a = APK(APK_PATH)
dexes = [DEX(b) for b in a.get_all_dex()]

def disasm(m, limit=500):
    out = []
    if not m.get_code(): return out
    for ins in m.get_code().get_bc().get_instructions():
        out.append(ins.get_name() + " " + str(ins.get_output())[:110])
        if len(out) >= limit: break
    return out

WANT = {"y": "onInflate", "s": "onCreate", "O": "getNavController",
        "t": "onCreateView", "r": "onAttach", "v": "???", "B": "onViewCreated", "E": "??2"}

for d in dexes:
    for c in d.get_classes():
        if c.get_name() == "Landroidx/navigation/fragment/NavHostFragment;":
            for m in c.get_methods():
                short = m.get_name()
                if short in WANT:
                    print(f"\n### {short} (={WANT[short]}) {m.get_descriptor()}")
                    for l in disasm(m): print("   ", l)
