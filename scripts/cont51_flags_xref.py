#!/usr/bin/env python3
"""cont51_ayh_scan.py — androguard xref census for the solitaire detach-IAE:
(1) all writers of ViewHolder.mFlags (ay$w.n) — who sets FLAG_IGNORE;
(2) all callers of ChildHelper.detachViewFromParent (ay$5.c(I))."""
import zipfile
from androguard.misc import AnalyzeDex

z = zipfile.ZipFile('upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk')
open('/tmp/sol71.dex', 'wb').write(z.read('classes.dex'))
a, d, dx = AnalyzeDex('/tmp/sol71.dex')

target_f = None
for f in d.get_fields():
    if f.get_class_name() == 'Landroid/support/v7/widget/ay$w;' and f.get_name() == 'n':
        target_f = f
        print('FIELD:', f.get_class_name(), f.get_name(), f.get_descriptor())
        break

if target_f is not None:
    print('== writers (iput-object xrefs) ==')
    for _, mref, off in dx.get_xref_field(target_f.get_field()):
        m = mref.get_method()
        print(f'  {m.get_class_name()}->{m.get_name()}{m.get_descriptor()}')

print()
print('== callers of ay$5.c(I) (ChildHelper.detachViewFromParent) ==')
for m in d.get_methods():
    if m.get_class_name() == 'Landroid/support/v7/widget/ay$5;' and m.get_name() == 'c':
        am = dx.get_method(m)
        for _, callsite, _off in am.get_xref_to():
            pass
        for cls, meth in am.get_xref_from():
            print(f'  called-from: {cls} -> {meth.get_name()}{meth.get_descriptor()}')
        break

print()
print('== readers of ay$w.r() (shouldIgnore) ==')
for m in d.get_methods():
    if m.get_class_name() == 'Landroid/support/v7/widget/ay$w;' and m.get_name() == 'r':
        am = dx.get_method(m)
        for cls, meth in am.get_xref_from():
            print(f'  caller: {cls} -> {meth.get_name()}{meth.get_descriptor()}')
        break
