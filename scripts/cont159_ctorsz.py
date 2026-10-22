#!/usr/bin/env python3
import struct, zipfile
d = zipfile.ZipFile('upload/canonical_apks/stack.tower3d_1.apk').read('classes.dex')
ctors = [('()V', 0x20983c), ('(I)V', 0x209930), ('(Lcom/badlogic/gdx/utils/Array;)V', 0x2098e4),
         ('(Ljava/lang/Class;)V', 0x20994c), ('(ZI)V', 0x20985c),
         ('(ZILjava/lang/Class;)V', 0x209880), ('(Z[Ljava/lang/Object;II)V', 0x2098ac),
         ('([Ljava/lang/Object;)V', 0x20996c)]
for sig, off in ctors:
    insns_sz = struct.unpack_from('<I', d, off + 12)[0]
    print('<init>' + sig, 'insns_units=', insns_sz)
