#!/usr/bin/env python3
"""CONT-14: DEX truth for the PagerTitleStrip.getDefaultColor NPE face.

Recurring ×2 census face (fossify_notes + batterymonitor):
  NPE 'invoke virtual Landroid/content/res/ColorStateList;.getDefaultColor
  on a null object reference' at Landroidx/viewpager/widget/PagerTitleStrip;
  .<init> pc=138.

Machine-verify from the APK bytes:
  1. which invoke feeds the CSL receiver (obtainStyledAttributes chain),
  2. which field stores it,
  3. the exact call site at pc=138,
  4. every path that can reach the null receiver.
"""
import sys, zipfile
from loguru import logger as _lg
_lg.remove()
from androguard.core.dex import DEX

APK = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/upload/fdroid_batch/codes.swistak.batterymonitor_1007003.apk"

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith(".dex")]
print("dex files:", dex_names)

TARGET = "Landroidx/viewpager/widget/PagerTitleStrip;"

found = None
for dn in dex_names:
    dex = DEX(z.read(dn))
    names = {c.get_name() for c in dex.get_classes()}
    hits = sorted(n for n in names if "PagerTitleStrip" in n)
    print(dn, "PagerTitleStrip hits:", hits)
    if TARGET in names:
        found = (dn, dex)
        break
if not found:
    print("TARGET class not present")
    sys.exit(0)
dn, dex = found

tnames = []
for c in dex.get_classes():
    if c.get_name() != TARGET:
        continue
    for m in c.get_methods():
        tnames.append((m.get_name(), m.get_descriptor(), bool(m.get_code())))
print("PagerTitleStrip methods:", tnames)

for c in dex.get_classes():
    if c.get_name() != TARGET:
        continue
    for m in c.get_methods():
        if m.get_name() not in ("<init>", "setTextColor", "updateText",
                                "onTextChanged", "updateTextColors"):
            continue
        code = m.get_code()
        if not code:
            continue
        print(f"\n===== {c.get_name()}.{m.get_name()}{m.get_descriptor()} "
              f"(regs={code.get_registers_size()}) =====")
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            out = ins.get_output()
            print(f"  {ins.get_offset():6x}: {op:28s} {out}")
