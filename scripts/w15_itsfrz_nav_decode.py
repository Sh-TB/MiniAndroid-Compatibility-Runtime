#!/usr/bin/env python3
"""W15 androguard recon #1: itsfrz (com.itsfrz.tictactoe) nav-lane decode.
Goal: NavHostFragment.onInflate contract + NavInflater/NavGraph death sites
(LC4/u;.s, LU1/r;.<init> pc=0x45 from W14 evidence).
"""
import json, sys, logging
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "/home/z/my-project/apk_cache/com.itsfrz.tictactoe_5.apk"
OUT = "/home/z/my-project/macr/evidence/w15/ITSFRZ_NAV_DECODE.json"

a = APK(APK_PATH)
report = {"apk": APK_PATH, "package": a.get_package()}

# 1. find the navigation XML resources
nav_xmls = []
for f in a.get_files():
    if f.startswith("res/") and f.endswith(".xml"):
        nav_xmls.append(f)
report["xml_count"] = len(nav_xmls)

# 2. DEX: find NavHostFragment subclass + onInflate + nav classes
dexes = []
for dex_bytes in (a.get_dex() if isinstance(a.get_dex(), list) else [a.get_dex()]):
    dexes.append(DEX(dex_bytes))

targets = []
for d in dexes:
    for c in d.get_classes():
        cn = c.get_name()
        s = str(c.get_superclassname())
        # NavHostFragment subclasses or nav package classes
        if ("NavHostFragment" in cn or "navigation" in cn.lower() or
            "NavHostFragment" in s):
            methods = []
            for m in c.get_methods():
                methods.append({
                    "name": m.get_name(),
                    "desc": m.get_descriptor(),
                    "size": len(m.get_code().get_bc().get_insn()) if m.get_code() else 0,
                })
            targets.append({"class": cn, "super": s, "methods": methods})

report["nav_classes"] = targets
print(json.dumps({"nav_class_count": len(targets),
                  "classes": [t["class"] for t in targets][:20]}, indent=1))

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(report, open(OUT, "w"), indent=1)
print("saved", OUT)
