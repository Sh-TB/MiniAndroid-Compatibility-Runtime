#!/usr/bin/env python3
# cont42_decode.py — CONT-42 Phase-1: static decode of
# com.tananaev.calculator v1.10's fragment path. Questions:
#  (1) MainActivity.onCreate: the exact FragmentTransaction call shape
#      (beginTransaction / add / commit order, container id, fragment class).
#  (2) The fragment class: superclass (platform android.app.Fragment?
#      platform PreferenceFragment?), overridden lifecycle methods.
#  (3) addPreferencesFromResource call sites + the XML resource id.
#  (4) Does the fragment override onCreateView (or does the platform
#      PreferenceFragment provide it)?
# Field-ref-exact against the real DEX. No guessing.
import zipfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/tmp/com.tananaev.calculator_11.apk'
z = zipfile.ZipFile(APK)
names = [n for n in z.namelist() if n.endswith('.dex')]
dexas = {n: DEX(z.read(n)) for n in names}
print("dex files:", names)

classes = []
for n, d in dexas.items():
    classes += list(d.get_classes())
print(f"classes: {len(classes)}")

def find_class(name_sub):
    for c in classes:
        if name_sub in c.get_name():
            yield c

# ── (1) FragmentTransaction census ───────────────────────────────────────
print("\n== FragmentTransaction / FragmentManager call census:")
ftx_sites = []
for c in classes:
    cn = c.get_name()
    for m in c.get_methods():
        code = m.get_code()
        if not code:
            continue
        for i in code.get_bc().get_instructions():
            op = i.get_name()
            if not op.startswith('invoke'):
                continue
            out = i.get_output()
            if 'Landroid/app/FragmentTransaction;' in out or \
               'Landroid/app/FragmentManager;' in out or \
               'addPreferencesFromResource' in out or \
               'getFragmentManager' in out:
                ftx_sites.append((cn, m.get_name(), out.strip()))
for s in ftx_sites:
    print("  ", s)

# ── (2) MainActivity disassembly ─────────────────────────────────────────
print("\n== MainActivity method bodies:")
for c in find_class('Lcom/tananaev/calculator/MainActivity;'):
    print("class:", c.get_name(), "extends", c.get_superclassname())
    for m in c.get_methods():
        print(f"\n--- {m.get_name()} {m.get_descriptor()} ---")
        code = m.get_code()
        if not code:
            print("   (abstract/native)")
            continue
        for i in code.get_bc().get_instructions():
            print("   ", i.get_name(), i.get_output())

# ── (3) Fragment subclasses + lifecycle overrides ────────────────────────
print("\n== Fragment/PreferenceFragment subclasses:")
for c in classes:
    sf = c.get_superclassname() or ''
    if 'Fragment' in sf and c.get_name().startswith('Lcom/tananaev'):
        print("class:", c.get_name(), "extends", sf)
        for m in c.get_methods():
            print(f"   method: {m.get_name()} {m.get_descriptor()}")

# ── (4) PreferenceFragment overrides in full detail ─────────────────────
print("\n== PreferenceFragment subclass bodies:")
for c in classes:
    sf = c.get_superclassname() or ''
    if 'PreferenceFragment' in sf:
        print("class:", c.get_name(), "extends", sf)
        for m in c.get_methods():
            print(f"\n--- {m.get_name()} {m.get_descriptor()} ---")
            code = m.get_code()
            if not code:
                continue
            for i in code.get_bc().get_instructions():
                print("   ", i.get_name(), i.get_output())
