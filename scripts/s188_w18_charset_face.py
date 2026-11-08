#!/usr/bin/env python3
"""S188-W18b: pin AssetLoaderService.createCharset pc=35 (the new p9 death
face: ARR-LEN-NULL after the Gdx2DPixmap/Matrix4 family went real)."""
import zipfile
from androguard.core.dex import DEX

apk = '/home/z/my-project/upload/stuck_apks/se.tube42.p9.android.apk'
z = zipfile.ZipFile(apk)
d = DEX(z.read('classes.dex'))

for cls in d.get_classes():
    cn = cls.get_name() or ''
    if cn != 'Lse/tube42/p9/logic/AssetLoaderService;':
        continue
    for m in cls.get_methods():
        if (m.get_name() or '') != 'createCharset':
            continue
        print('===', cn, m.get_name(), m.get_descriptor())
        code = m.get_code()
        pc = 0
        for ins in code.get_bc().get_instructions():
            ln = ins.get_length()
            mark = ' <<<< pc=35' if pc == 35 else ''
            print(f'  pc={pc:4d} {ins.get_name():18s} {ins.get_output()[:130]}{mark}')
            pc += ln
