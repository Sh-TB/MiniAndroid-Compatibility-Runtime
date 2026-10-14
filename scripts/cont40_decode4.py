#!/usr/bin/env python3
# cont40_decode4.py — Lr;->onAttachedToWindow, Lr;->j() (the recomposer
# resolution chain), Lr;->onDetachedFromWindow (token field reader), and a
# census of readers of the token field Lr;->f.
import zipfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

for c in d.get_classes():
    cn = c.get_name()
    if cn == 'Lr;':
        for m in c.get_methods():
            if m.get_name() in ('onAttachedToWindow', 'j', 'onDetachedFromWindow'):
                code = m.get_code()
                print(f"\n== Lr;->{m.get_name()}{m.get_descriptor()}")
                if not code:
                    print("   (abstract)")
                    continue
                idx = 0; n = 0
                for i in code.get_bc().get_instructions():
                    if n >= 90: print("   ..."); break
                    print(f"   {idx:4d} {i.get_name():<24} {i.get_output()[:96]}")
                    idx += i.get_length() // 2 if i.get_length() >= 2 else 1
                    n += 1

# census: readers of Lr;->f (the previousAttachedWindowToken field)
print("\n== readers of field Lr;->f Landroid/os/IBinder;:")
for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if not code: continue
        for i in code.get_bc().get_instructions():
            out = i.get_output()
            if 'Lr;->f' in out and i.get_name().startswith('iget'):
                print(f"   {c.get_name()}->{m.get_name()}  {i.get_name()}")
