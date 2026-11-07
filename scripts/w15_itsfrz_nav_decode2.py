#!/usr/bin/env python3
"""W15 androguard recon #2: itsfrz NavHostFragment.onInflate + nav graph XML + NavController chain."""
import json, logging, zipfile, re
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk"
a = APK(APK_PATH)

# --- 1. all dex classes: nav + the R8-death classes from W14 evidence ---
dexes = [DEX(b) for b in a.get_all_dex()]
interesting = {}
WANT = ("Landroidx/navigation/fragment/NavHostFragment;",
        "Landroidx/navigation/NavController;",
        "Landroidx/navigation/NavInflater;")

def disasm(m, limit=200):
    out = []
    if not m.get_code(): return out
    for ins in m.get_code().get_bc().get_instructions():
        out.append(ins.get_name() + " " + str(ins.get_output())[:90])
        if len(out) >= limit: break
    return out

for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        if cn in WANT:
            interesting[cn] = {}
            for m in c.get_methods():
                if m.get_name() in ("onInflate", "onCreate", "onCreateView", "inflate", "<init>", "setGraph", "create", "onAttach"):
                    interesting[cn][m.get_name() + m.get_descriptor()[:40]] = disasm(m)

print("== NavHostFragment.onInflate ==")
for k, v in interesting.get("Landroidx/navigation/fragment/NavHostFragment;", {}).items():
    if k.startswith("onInflate"):
        print("### ", k)
        for l in v[:60]: print("   ", l)

# --- 2. the nav graph XML: search res/*.xml for navigation root ---
z = zipfile.ZipFile(APK_PATH)
nav_candidates = []
for n in z.namelist():
    if n.startswith("res/") and n.endswith(".xml"):
        head = z.read(n)[:400]
        if b"navigation" in head and (b"NavHost" in head or b"fragment" in head or b"startDestination" in head.lower() or b"startDestination" in head):
            nav_candidates.append(n)
print("\n== nav graph candidates ==", nav_candidates)

# --- 3. main activity layout: FragmentContainerView usage ---
layouts = []
for n in z.namelist():
    if n.startswith("res/layout") and n.endswith(".xml"):
        data = z.read(n)
        if b"FragmentContainerView" in data or b"NavHostFragment" in data:
            layouts.append(n)
print("== layouts with FCV/NavHost ==", layouts)
