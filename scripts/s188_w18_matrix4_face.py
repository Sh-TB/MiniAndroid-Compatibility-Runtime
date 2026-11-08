#!/usr/bin/env python3
"""S188-W18: pin the Matrix4 call face from the DEX (androguard oracle).

Questions the run raised:
  1. Which `mul` overloads exist in p9's bundled Matrix4 (names/descs/
     access flags)? The runtime bridged sig=([F[F)V — is that the private
     native mul([F[F)[F or something else?
  2. What does Matrix4.setToLookAt bytecode do — which mul does it call
     and with which registers?
  3. What does Matrix4.mul(Matrix4) (the wrapper) look like — does it
     assign `val = mul(val, matrix.val)` (native returns jfloatArray!)?
  4. OrthographicCamera.update call site shape.
"""
import sys, re
from androguard.core.dex import DEX

apk = '/home/z/my-project/upload/stuck_apks/se.tube42.p9.android.apk'
import zipfile
z = zipfile.ZipFile(apk)
d = DEX(z.read('classes.dex'))

WANT = {
    'Lcom/badlogic/gdx/math/Matrix4;': None,          # all methods
    'Lcom/badlogic/gdx/graphics/OrthographicCamera;': ['update', 'setToRotation', 'rotate'],
}
MUL_SHAPES = []

for cls in d.get_classes():
    cn = cls.get_name() or ''
    if cn not in WANT:
        continue
    wanted = WANT[cn]
    for m in cls.get_methods():
        name = m.get_name() or ''
        desc = m.get_descriptor() or ''
        if wanted is not None and name not in wanted and 'mul' not in name \
           and 'setToLookAt' not in name:
            continue
        acc = m.get_access_flags_string() or ''
        if 'mul' in name or name == 'setToLookAt' or cn.endswith('OrthographicCamera;') and name == 'update':
            print(f'\n=== {cn} {name} {desc} [{acc}]')
            code = m.get_code()
            if code is None:
                print('  <abstract/native>')
                if 'native' in acc:
                    MUL_SHAPES.append((cn, name, desc))
                continue
            for ins in code.get_bc().get_instructions():
                op = ins.get_name()
                out = ins.get_output()
                if op.startswith('invoke') or op in ('iget-object', 'sget-object', 'iput-object', 'sput-object', 'new-array', 'array-length'):
                    print(f'  {op:14s} {out[:150]}')

print('\n--- native mul shapes (dex) ---')
for s in MUL_SHAPES:
    print(s)
