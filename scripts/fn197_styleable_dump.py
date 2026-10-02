#!/usr/bin/env python3
"""F-NEW-197 ground truth: dump Ll1/d; static field values (the styleable
int[] R$styleable equivalent) from opencalculator_53.apk classes.dex."""
import struct, zipfile

APK = '/home/z/my-project/upload/opencalculator_53.apk'
TARGET = 'Ll1/d;'

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

def main():
    z = zipfile.ZipFile(APK)
    d = z.read('classes.dex')
    ssz, soff = struct.unpack_from('<II', d, 0x38)
    strs = []
    for i in range(ssz):
        so = struct.unpack_from('<I', d, soff + i*4)[0]
        ln, doff = uleb(d, so)
        strs.append(d[doff:doff+ln*4].decode('utf-8', errors='replace').split('\x00')[0])
    tsz, toff = struct.unpack_from('<II', d, 0x40)
    types = [strs[struct.unpack_from('<I', d, toff + i*4)[0]] for i in range(tsz)]
    fsz, foff = struct.unpack_from('<II', d, 0x50)
    fields = []
    for i in range(fsz):
        cls, typ, nm = struct.unpack_from('<HHI', d, foff + i*8)
        fields.append((types[cls], types[typ], strs[nm]))
    cdsz, cdoff = struct.unpack_from('<II', d, 0x60)
    for i in range(cdsz):
        cd = cdoff + i*32
        cls_idx = struct.unpack_from('<I', d, cd)[0]
        if types[cls_idx] != TARGET: continue
        statics_off = struct.unpack_from('<I', d, cd + 16)[0]  # static_values_off
        cdo = struct.unpack_from('<I', d, cd + 24)[0]
        print('class_data_off=', hex(cdo), 'static_values_off=', hex(statics_off))
        off = cdo
        sf, off = uleb(d, off); inf, off = uleb(d, off); dm, off = uleb(d, off); vm, off = uleb(d, off)
        print('static fields:', sf, 'instance:', inf)
        # static field list (idx diffs)
        fidx = 0; names = []
        for _ in range(sf):
            dlt, off = uleb(d, off); fidx += dlt
            acc, off = uleb(d, off)
            names.append(fields[fidx])
        for n in names[:12]:
            print('  field:', n)
        # decode static_values encoded_array
        if statics_off:
            off = statics_off
            cnt, off = uleb(d, off)
            print('static_values count:', cnt)
            for k in range(min(cnt, len(names), 12)):
                # encoded_value header
                b = d[off]
                vtype = b & 0x1f
                varg = (b >> 5) & 0x7
                off += 1
                if vtype == 0x1e:  # ARRAY
                    sz2, off = uleb(d, off)
                    vals = []
                    for j in range(sz2):
                        b2 = d[off]; t2 = b2 & 0x1f; g2 = (b2 >> 5) & 0x7; off += 1
                        raw = int.from_bytes(d[off:off+g2+1], 'little'); off += g2 + 1
                        if t2 in (0x04,):  # INT
                            v = struct.unpack('<i', d[off-g2-1:off])[0]
                            vals.append(f'{v:#x}')
                        else:
                            vals.append(f't={t2:#x} raw={raw:#x}')
                    print(f'  {names[k][2]}: ARRAY[{sz2}] = {vals}')
                elif vtype == 0x00:  # BYTE
                    raw = int.from_bytes(d[off:off+varg+1], 'little'); off += varg + 1
                    print(f'  {names[k][2]}: byte {raw}')
                elif vtype == 0x04:  # INT
                    raw = int.from_bytes(d[off:off+varg+1], 'little'); off += varg + 1
                    v = struct.unpack('<i', struct.pack('<I', raw & 0xffffffff))[0]
                    print(f'  {names[k][2]}: int {v} ({v:#x})')
                elif vtype == 0x02:  # CHAR/SHORT?
                    raw = int.from_bytes(d[off:off+varg+1], 'little'); off += varg + 1
                    print(f'  {names[k][2]}: t2 raw {raw:#x}')
                else:
                    print(f'  {names[k][2]}: vtype={vtype:#x} varg={varg} (skip)')
                    off += varg + 1
        return

if __name__ == '__main__':
    main()
