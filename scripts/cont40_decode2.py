#!/usr/bin/env python3
# cont40_decode2.py — CONT-40 Phase-1b: disassemble the exact attach chain.
# Lr; (AbstractComposeView, extends ViewGroup): onAttachedToWindow / c / e / k
# / setParentContext. Le81; (extends Lr;): onAttachedToWindow. Lho;.setContent.
# The two other getWindowToken sites (Ldo1;->e, Lwo1;->e).
import zipfile, sys
from androguard.core.dex import DEX

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

WANT = {
    'Lr;': ['onAttachedToWindow', 'c', 'e', 'k', 'setParentContext'],
    'Le81;': ['onAttachedToWindow', '<init>', 'setContent'],
    'Lho;': ['setContent', 'onAttachedToWindow'],
    'Ldo1;': ['e'],
    'Lwo1;': ['e'],
}

for c in d.get_classes():
    cn = c.get_name()
    if cn not in WANT:
        continue
    for m in c.get_methods():
        if m.get_name() not in WANT[cn]:
            continue
        code = m.get_code()
        print(f"\n== {cn}->{m.get_name()}{m.get_descriptor()} regs={code.get_registers_size() if code else 0}")
        if not code:
            print("   (no code — abstract)")
            continue
        idx = 0
        for i in code.get_bc().get_instructions():
            print(f"   {idx:4d} {i.get_name():<24} {i.get_output()[:100]}")
            idx += i.get_length() // 2 if i.get_length() >= 2 else 1
