#!/usr/bin/env python3
"""S188-W18b: who calls createCharset and where does the String[] come from."""
import zipfile, re
from androguard.core.dex import DEX

apk = '/home/z/my-project/upload/stuck_apks/se.tube42.p9.android.apk'
z = zipfile.ZipFile(apk)
d = DEX(z.read('classes.dex'))

TARGET = 'Lse/tube42/p9/logic/AssetLoaderService;->createCharset'

for cls in d.get_classes():
    cn = cls.get_name() or ''
    for m in cls.get_methods():
        code = m.get_code()
        if code is None:
            continue
        txts = []
        hit = False
        pc = 0
        for ins in code.get_bc().get_instructions():
            out = str(ins.get_output())
            if 'createCharset' in out:
                hit = True
                txts.append((pc, ins.get_name(), out))
            pc += ins.get_length()
        if hit:
            print(f'=== caller {cn} {m.get_name()} {m.get_descriptor()}')
            # print full method bytecode for context
            pc = 0
            for ins in code.get_bc().get_instructions():
                out = str(ins.get_output())
                mark = ' <<<' if any(p == pc for p, _, _ in txts) else ''
                print(f'  pc={pc:4d} {ins.get_name():20s} {out[:120]}{mark}')
                pc += ins.get_length()
            print()
