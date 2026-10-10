#!/usr/bin/env python3
# cont40_decode5.py — full Lr;->k() (all pcs), Lp;->run(), La72;->a.
import zipfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

WANT = {('Lr;', 'k'), ('Lp;', 'run'), ('La72;', 'a')}
for c in d.get_classes():
    cn = c.get_name()
    for m in c.get_methods():
        if (cn, m.get_name()) not in WANT:
            continue
        code = m.get_code()
        print(f"\n== {cn}->{m.get_name()}{m.get_descriptor()}")
        if not code:
            print("   (abstract)")
            continue
        idx = 0; n = 0
        for i in code.get_bc().get_instructions():
            if n >= 160: print("   ..."); break
            print(f"   {idx:4d} {i.get_name():<24} {i.get_output()[:95]}")
            idx += i.get_length() // 2 if i.get_length() >= 2 else 1
            n += 1
