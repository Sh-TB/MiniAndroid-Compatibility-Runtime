#!/usr/bin/env python3
# cont44_b_tan_decode.py — CONT44-B DECODE 1 (F-NEW-305):
# static decode of the appcompat inset chain inside
# com.tananaev.calculator_11.apk. Questions:
#  (1) ActionBarOverlayLayout: which methods exist (onMeasure / onLayout /
#      onApplyWindowInsets / fitSystemWindows / actionbar fields), and what
#      the REAL bytecode does with the action-bar measured height.
#  (2) ContentFrameLayout: does it override any inset entry point
#      (onApplyWindowInsets / fitSystemWindows)?
#  (3) The sub-decor XML (abc_screen_toolbar / abc_screen_simple): the
#      ContentFrameLayout attributes (fitsSystemWindows?).
#  (4) The app's own classes: does anything app-side call setInsets /
#      fitSystemWindows / onApplyWindowInsets?
# Field-ref-exact against the real DEX. No guessing.
import zipfile, re
from collections import defaultdict
from androguard.core.dex import DEX

APK = '/home/z/my-project/tmp/com.tananaev.calculator_11.apk'
z = zipfile.ZipFile(APK)
dexnames = [n for n in z.namelist() if n.endswith('.dex')]
dexas = {n: DEX(z.read(n)) for n in dexnames}
print("dex files:", dexnames)

classes = []
for n, d in dexas.items():
    classes += list(d.get_classes())
print("classes:", len(classes))
by_name = {c.get_name(): c for c in classes}

def dump_method(cls_name, meth_name, max_ins=4000):
    c = by_name.get(cls_name)
    if not c:
        print(f"!! class {cls_name} NOT FOUND")
        return
    for m in c.get_methods():
        if m.get_name() != meth_name:
            continue
        print(f"\n--- {cls_name}.{m.get_name()} {m.get_descriptor()} ---")
        code = m.get_code()
        if not code:
            print("   (no code)")
            continue
        n_ins = 0
        for i in code.get_bc().get_instructions():
            print("   ", i.get_name(), i.get_output())
            n_ins += 1
            if n_ins >= max_ins:
                print("    ... (truncated)")
                break
        return
    print(f"!! method {meth_name} NOT FOUND in {cls_name}")

def method_list(cls_name):
    c = by_name.get(cls_name)
    if not c:
        print(f"!! class {cls_name} NOT FOUND")
        return
    print(f"\n== {cls_name} extends {c.get_superclassname()} methods:")
    for m in c.get_methods():
        print(f"   {m.get_name()} {m.get_descriptor()}")

def field_list(cls_name):
    c = by_name.get(cls_name)
    if not c:
        return
    print(f"\n== {cls_name} fields:")
    for f in c.get_fields():
        print(f"   {f.get_name()} {f.get_descriptor()}")

# ── (1) ActionBarOverlayLayout ──────────────────────────────────────────
ABOL = 'Landroidx/appcompat/widget/ActionBarOverlayLayout;'
method_list(ABOL)
field_list(ABOL)

# Inset-relevant method bodies (disassembled; these decide the content top)
for meth in ('onMeasure', 'onLayout', 'onApplyWindowInsets',
             'fitSystemWindows', 'fitSystemWindowsInt',
             'pullChildren', 'requestFitSystemWindows',
             'computeSystemWindowInsets', 'onWindowInsetsChanged'):
    dump_method(ABOL, meth)

# ── (2) ContentFrameLayout inset overrides ──────────────────────────────
CFL = 'Landroidx/appcompat/widget/ContentFrameLayout;'
method_list(CFL)
dump_method(CFL, 'onApplyWindowInsets')
dump_method(CFL, 'fitSystemWindows')

# ── (3) census: who references the inset APIs across the whole DEX ──────
print("\n== inset-API xref census (whole APK):")
faces = ('onApplyWindowInsets', 'fitSystemWindows', 'setInsets',
         'getSystemWindowInsetTop', 'consumeSystemWindowInsets',
         'dispatchApplyWindowInsets', 'replaceSystemWindowInsets')
xref = defaultdict(set)
for c in classes:
    cn = c.get_name()
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        for i in code.get_bc().get_instructions():
            out = i.get_output()
            for f in faces:
                if f in out:
                    xref[f].add(f"{cn}.{m.get_name()}")
for f in faces:
    sites = sorted(xref.get(f, ()))
    print(f"  {f}: {len(sites)} sites")
    for s in sites[:12]:
        print(f"     {s}")

# ── (4) the app's own classes ───────────────────────────────────────────
print("\n== com.tananaev.calculator classes:")
for c in classes:
    if c.get_name().startswith('Lcom/tananaev'):
        print("  ", c.get_name(), "extends", c.get_superclassname())
        for m in c.get_methods():
            print(f"      {m.get_name()} {m.get_descriptor()}")

# ── (5) sub-decor XML attributes (fitsSystemWindows on ContentFrameLayout)
print("\n== res/layout xml entries:")
arsc_names = [n for n in z.namelist() if n.startswith('res/layout')]
for n in sorted(arsc_names):
    if 'toolbar' in n or 'screen' in n:
        data = z.read(n)
        # AXML string-pool scan: find attribute names present
        strings = re.findall(rb'[\x20-\x7e]{6,}', data[:20000])
        ss = [s.decode() for s in strings]
        marks = [s for s in ss if 'fitsSystemWindows' in s or 'ContentFrame' in s
                 or 'ActionBarOverlay' in s or 'action_bar' in s]
        print(f"  {n}: {marks[:8]}")
