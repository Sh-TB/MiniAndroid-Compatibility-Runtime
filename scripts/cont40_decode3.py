#!/usr/bin/env python3
# cont40_decode3.py — Lr;->g() (ensureCompositionCreated), Lr;->l() (the
# composition-context/recomposer resolution), onDetachedFromWindow (the
# token-field consumer), Le81; attach, Lho;.setContent.
import zipfile
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

WANT = {
    'Lr;': ['g', 'l', 'onDetachedFromWindow', 'onWindowVisibilityChanged',
            'setPreviousAttachedWindowToken', 'getShouldCreateCompositionOnAttachedToWindow'],
    'Le81;': ['onAttachedToWindow', 'setContent'],
    'Lho;': ['setContent'],
}
MAXI = 70

for c in d.get_classes():
    cn = c.get_name()
    if cn not in WANT:
        continue
    for m in c.get_methods():
        if m.get_name() not in WANT[cn]:
            continue
        code = m.get_code()
        print(f"\n== {cn}->{m.get_name()}{m.get_descriptor()}")
        if not code:
            print("   (abstract)")
            continue
        idx = 0
        n = 0
        for i in code.get_bc().get_instructions():
            if n >= MAXI:
                print(f"   ... ({idx}+)")
                break
            print(f"   {idx:4d} {i.get_name():<24} {i.get_output()[:96]}")
            idx += i.get_length() // 2 if i.get_length() >= 2 else 1
            n += 1
