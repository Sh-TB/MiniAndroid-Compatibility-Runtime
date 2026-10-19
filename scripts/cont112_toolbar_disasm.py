#!/usr/bin/env python3
# cont112_toolbar_disasm.py — F-NEW-448 layer-2 ground truth (CONT-112 W1).
# Decode the chess (jwtc 298) androidx appcompat Toolbar DEX:
#   1. Which ctor runs for the XML-inflated Toolbar (2-arg delegate chain)?
#   2. Does Toolbar.onMeasure max() against getSuggestedMinimumHeight() /
#      getMinimumHeight() (the layer-1 shadows), its own mMinHeight field,
#      or nothing?
#   3. Does the ctor read Toolbar_minHeight from obtainStyledAttributes?
# AOSP refs: View.java ctor reads R.styleable.View (android:minWidth/
# minHeight) -> setMinimumWidth/Height; appcompat Toolbar ctor reads
# R.styleable.Toolbar_minHeight into mMinHeight.
import sys
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from androguard.misc import AnalyzeAPK

APK = "upload/chess_jwtc_298.apk"
a, d, dx = AnalyzeAPK(APK)

TB = "Landroidx/appcompat/widget/Toolbar;"

def find_method(cls, name):
    for m in dx.get_methods():
        if m.is_external():
            continue
        meth = m.get_method()
        if meth.get_class_name() == cls and meth.get_name() == name:
            return m
    return None

def dump(meth, show_cmp=True, max_ins=100000):
    m = meth.get_method()
    print("=" * 78)
    print("METHOD", m.get_class_name(), "->", m.get_descriptor())
    code = m.get_code()
    if not code:
        print("  <no code>")
        return
    idx = 0
    n = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        out = f"  @{idx:6d} {op} {ins.get_output()}"
        if show_cmp and any(k in op for k in (
                "invoke", "sget", "iget", "const", "sput", "iput")):
            print(out)
            n += 1
        idx += ins.get_length()
        if n > max_ins:
            break

# 1) ctor signatures present
print("### Toolbar ctor overloads present in DEX:")
for m in dx.get_methods():
    if m.is_external():
        continue
    meth = m.get_method()
    if meth.get_class_name() == TB and meth.get_name() == "<init>":
        print("  ", meth.get_descriptor())

# 2) onMeasure
om = find_method(TB, "onMeasure")
if om:
    dump(om)
else:
    print("Toolbar.onMeasure NOT FOUND")

# 3) the 3-arg ctor: look for obtainStyledAttributes + minHeight reads
c3 = None
for m in dx.get_methods():
    if m.is_external():
        continue
    meth = m.get_method()
    if meth.get_class_name() == TB and meth.get_name() == "<init>":
        desc = meth.get_descriptor()
        if "(Landroid/content/Context;Landroid/util/AttributeSet;I)" in desc:
            c3 = meth
if c3:
    src = c3.get_method()
    print("=" * 78)
    print("### 3-arg ctor — styleable/minHeight-relevant slice:")
    code = src.get_code()
    idx = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        out = ins.get_output()
        if any(k in op for k in ("invoke", "sget")) and (
                "obtainStyledAttributes" in out or "toolbarStyle" in out
                or "Toolbar" in out or "minHeight" in out or "styleable" in out):
            print(f"  @{idx:6d} {op} {out}")
        idx += ins.get_length()

# 4) does any Toolbar method call getSuggestedMinimumHeight?
print("=" * 78)
print("### Toolbar-family callsites of suggested/minimum height:")
for m in dx.get_methods():
    if m.is_external():
        continue
    meth = m.get_method()
    if not meth.get_class_name().startswith("Landroidx/appcompat/widget/"):
        continue
    code = meth.get_code()
    if not code:
        continue
    idx = 0
    for ins in code.get_bc().get_instructions():
        if ins.get_name().startswith("invoke"):
            out = ins.get_output()
            if "getSuggestedMinimumHeight" in out or \
               "getSuggestedMinimumWidth" in out or \
               "getMinimumHeight" in out or \
               "setMinimumHeight" in out:
                print("  ", meth.get_class_name(), "->",
                      meth.get_descriptor(), "calls", out.strip())
        idx += ins.get_length()
print("done")
