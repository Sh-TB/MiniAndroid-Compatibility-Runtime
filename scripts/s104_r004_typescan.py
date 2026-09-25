#!/usr/bin/env python3
"""S104 R-004 CLASS-IDENTITY: regenerate the mapped-away-class type-scan
over the 54 census APKs (bytecode-accurate via androguard).

For each APK:
  1. which mapped-away REAL descriptors (androidx/material widget family the
     inflater maps to platform widgets) are DEFINED in the APK dex;
  2. which of them are type-tested (instance-of / check-cast / const-class)
     in app bytecode — i.e. app code relies on the real class identity.
Output: run/s104/r004_typescan.json
"""
import glob, json, os, zipfile as zfmod
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APKS = sorted(glob.glob("/home/z/my-project/run/s99/apks/*.apk"))

# layout_inflater.cpp KNOWN-map entries that map a REAL bundled class away
MAPPED_AWAY = [
    "Landroidx/appcompat/widget/AppCompatTextView;",
    "Landroidx/appcompat/widget/AppCompatButton;",
    "Landroidx/appcompat/widget/AppCompatEditText;",
    "Landroidx/appcompat/widget/AppCompatImageView;",
    "Landroidx/appcompat/widget/AppCompatCheckBox;",
    "Landroidx/appcompat/widget/AppCompatRadioButton;",
    "Landroidx/appcompat/widget/AppCompatSpinner;",
    "Lcom/google/android/material/button/MaterialButton;",
    "Lcom/google/android/material/textfield/MaterialAutoCompleteTextView;",
    "Lcom/google/android/material/textfield/TextInputEditText;",
    "Lcom/google/android/material/floatingactionbutton/FloatingActionButton;",
]

out = []
for apk in APKS:
    row = {"apk": os.path.basename(apk), "defined": [], "typetested": []}
    try:
        zf = zfmod.ZipFile(apk)
    except Exception as e:
        row["error"] = str(e)
        out.append(row)
        continue
    try:
        defined_set = set()
        tested = {}
        for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
            d = DEX(zf.read(name))
            # class defs
            for c in d.get_classes():
                cn = c.get_name()
                if cn in MAPPED_AWAY and cn not in defined_set:
                    defined_set.add(cn)
            # bytecode type refs (instance-of 0x20 / check-cast 0x1f / const-class 0x1c)
            for c in d.get_classes():
                for m in c.get_methods():
                    code = m.get_code()
                    if not code:
                        continue
                    for ins in m.get_instructions():
                        op = ins.get_name()
                        if op in ("instance-of", "check-cast", "const-class"):
                            try:
                                last = ins.get_operands()[-1]
                                tidx = last[1]
                                tname = d.get_type(tidx)
                            except Exception:
                                continue
                            if tname in MAPPED_AWAY and tname not in tested:
                                tested[tname] = op
        row["defined"] = sorted(defined_set)
        row["typetested"] = sorted(tested)
    except Exception as e:
        row["error"] = str(e)
    out.append(row)

os.makedirs("/home/z/my-project/run/s104", exist_ok=True)
with open("/home/z/my-project/run/s104/r004_typescan.json", "w") as f:
    json.dump(out, f, indent=1)

n_def = sum(1 for r in out if r.get("defined"))
n_test = sum(1 for r in out if r.get("typetested"))
print(f"APKs scanned: {len(out)}")
print(f"APKs defining >=1 mapped-away class: {n_def}")
print(f"APKs TYPE-TESTING >=1 mapped-away class: {n_test}")
from collections import Counter
cnt = Counter()
for r in out:
    for t in r.get("typetested", []):
        cnt[t] += 1
print("per-class type-test fan-out:")
for t, c in cnt.most_common():
    print(f"  {c:3d}  {t}")
