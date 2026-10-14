#!/usr/bin/env python3
"""cont23_dexinfo.py — lightweight DEX class info probe (superclass, interfaces, source file, method list).

Usage: python3 scripts/cont23_dexinfo.py <apk> Lcls; [--methods]
Searches all classes*.dex entries in the APK.
"""
import zipfile, struct, sys

def u4(b, o): return struct.unpack_from('<I', b, o)[0]
def u2(b, o): return struct.unpack_from('<H', b, o)[0]

class Dex:
    def __init__(self, data):
        self.d = data
        self.string_ids_size = u4(data, 0x38); self.string_ids_off = u4(data, 0x3C)
        self.type_ids_size = u4(data, 0x40); self.type_ids_off = u4(data, 0x44)
        self.field_ids_off = u4(data, 0x54); self.field_ids_size = u4(data, 0x50)
        self.method_ids_off = u4(data, 0x5C); self.method_ids_size = u4(data, 0x58)
        self.class_defs_off = u4(data, 0x64); self.class_defs_size = u4(data, 0x60)

    def get_string(self, idx):
        off = u4(self.d, self.string_ids_off + 4*idx)
        p = off; result = 0; shift = 0
        while True:
            b = self.d[p]; p += 1
            result |= (b & 0x7f) << shift; shift += 7
            if not (b & 0x80): break
        end = self.d.find(b'\x00', p)
        return self.d[p:end].decode('utf-8', 'replace')

    def get_type(self, idx):
        try:
            return self.get_string(u4(self.d, self.type_ids_off + 4*idx))
        except Exception:
            return f'<type:{idx}>'

    def find_class(self, name):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            if self.get_type(u4(self.d, off)) == name:
                return off
        return None

    def class_info(self, off, methods=False):
        d = self.d
        cls = self.get_type(u4(d, off))
        access = u4(d, off+4)
        sup = u4(d, off+8)
        ifo = u4(d, off+12)
        src = u4(d, off+16)
        out = [f'class {cls} access=0x{access:x} super={self.get_type(sup) if sup != 0xffffffff else "<none>"} '
               f'source={self.get_string(src) if src != 0xffffffff else "?"}']
        if ifo:
            n = u4(d, ifo)
            out.append('  interfaces: ' + ', '.join(self.get_type(u4(d, ifo+4*(j+1))) for j in range(n)))
        if methods:
            # class_data_off
            cdo = u4(d, off+24)
            if cdo:
                p = cdo
                def uleb(p):
                    r = 0; s = 0
                    while True:
                        b = d[p]; p += 1
                        r |= (b & 0x7f) << s; s += 7
                        if not (b & 0x80): break
                    return r, p
                sf, p = uleb(p); inf, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
                midx = 0
                for _ in range(dm):
                    didx_diff, p = uleb(p); acc, p = uleb(p)
                    midx += didx_diff
                out.append(f'  virtual methods ({vm}):')
                for _ in range(vm):
                    didx_diff, p = uleb(p); acc, p = uleb(p)
                    midx += didx_diff
                    moff = self.method_ids_off + 8*midx
                    cls_t = self.get_type(u2(d, moff))
                    proto = u2(d, moff+2)
                    nm = self.get_string(u4(d, moff+4))
                    out.append(f'    {cls_t}.{nm}')
            else:
                out.append('  (no class_data)')
        return '\n'.join(out)

def main():
    apk = sys.argv[1]
    target = sys.argv[2]
    show_methods = '--methods' in sys.argv
    with zipfile.ZipFile(apk) as z:
        for n in z.namelist():
            if n.endswith('.dex'):
                dx = Dex(z.read(n))
                off = dx.find_class(target)
                if off is not None:
                    print(f'[{n}]')
                    print(dx.class_info(off, methods=show_methods))
                    return
    print(f'{target} not found')

if __name__ == '__main__':
    main()
