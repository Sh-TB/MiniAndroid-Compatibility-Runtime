#!/usr/bin/env python3
"""CONT-8 W4: map Dooz R8 class names for the Compose draw path.
Anchor: Lt4; = AndroidComposeView (extends ViewGroup, dispatchDraw).
Goal: find (1) Lt4;<init> field/ctor chain -> root LayoutNode class,
(2) LayoutNode draw/measure methods, (3) UiApplier, (4) ComposerImpl emission."""
import sys, zipfile, re
sys.path.insert(0, '/home/z/my-project/tmp/w4venv/lib/python3.12/site-packages')
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

def load_dexs():
    out = []
    with zipfile.ZipFile(APK) as z:
        names = [n for n in z.namelist() if re.match(r'classes\d*\.dex$', n)]
        for n in sorted(names):
            out.append((n, DEX(z.read(n))))
    return out

dexs = load_dexs()
print(f"loaded {len(dexs)} dex files")

def find_class(name):
    for n, d in dexs:
        for c in d.get_classes():
            if c.get_name() == name:
                return n, c
    return None, None

# 1) Lt4; fields summary (done above); now: T0/C0 = Ltv0; x2 fields
# Ltv0; is likely the Owner (AndroidComposeView holds Owner) OR LayoutNode.
# Compose AndroidComposeView: `override val root = LayoutNode()` (LayoutNode field)
# + viewRootForInspector etc. Two Ltv0 fields -> maybe root + nested.

for target in ['Ltv0;']:
    _, c = find_class(target)
    if not c:
        print(f"{target} NOT FOUND"); continue
    print(f"\n=== {target} ===")
    print("super:", c.get_superclassname())
    print("interfaces:", list(c.get_interfaces())[:12])
    flds = list(c.get_fields())
    print(f"fields ({len(flds)}):")
    for f in flds[:25]:
        print(f"  {f.get_name()} : {f.get_descriptor()}")
    print("methods:")
    for m in c.get_methods():
        cl = m.get_code() and m.get_code().get_length() or 0
        print(f"  {m.get_name()} {m.get_descriptor()}  codelen={cl}")
