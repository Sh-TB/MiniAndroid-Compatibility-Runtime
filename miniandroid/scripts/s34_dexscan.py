#!/usr/bin/env python3
"""S34 R-NEW-333: correct DEX method_ids scan (layout: class u16, proto u16,
name u32 — prior scanner mis-decoded, hence 'setGraph' false-negative).
Modes:
  sig <Lret;> <param1> [param2...]   — find methods with exact return+params
  callers <name>                      — methods named <name> + code refs
Prints owner class + method name; DEX ground truth, no guessing.
"""
import struct, sys, zipfile

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def uleb_from(d, off):
    r = 0; sh = 0; p = off
    while True:
        b = d[p]; p += 1
        r |= (b & 0x7f) << sh; sh += 7
        if not (b & 0x80):
            break
    return r, p


class Dex:
    def __init__(self, data):
        self.d = data
        (self.str_n, self.str_o) = struct.unpack_from('<II', data, 0x38)
        (self.type_n, self.type_o) = struct.unpack_from('<II', data, 0x40)
        (self.proto_n, self.proto_o) = struct.unpack_from('<II', data, 0x48)
        (self.fid_n, self.fid_o) = struct.unpack_from('<II', data, 0x50)
        (self.mid_n, self.mid_o) = struct.unpack_from('<II', data, 0x58)
        (self.cls_n, self.cls_o) = struct.unpack_from('<II', data, 0x60)

    def string(self, idx):
        off = struct.unpack_from('<I', self.d, self.str_o + idx * 4)[0]
        _, p = uleb_from(self.d, off)
        end = self.d.index(b'\x00', p)
        return self.d[p:end].decode('utf-8', 'replace')

    def type(self, idx):
        return self.string(struct.unpack_from('<I', self.d, self.type_o + idx * 4)[0])

    def method_ids(self):
        """yield (idx, class_desc, proto_desc, name)"""
        for i in range(self.mid_n):
            off = self.mid_o + i * 8
            cls_t, proto_t, name_i = struct.unpack_from('<HHI', self.d, off)
            yield i, self.type(cls_t), self.proto_desc(proto_t), self.string(name_i)

    def proto_desc(self, idx):
        base = self.proto_o + idx * 8
        ret_t = struct.unpack_from('<H', self.d, base + 2)[0]
        po = struct.unpack_from('<I', self.d, base + 4)[0]
        if po == 0:
            params = []
        else:
            n = struct.unpack_from('<I', self.d, po)[0]
            pp = po + 4
            params = [self.type(struct.unpack_from('<H', self.d, pp + k * 2)[0])
                      for k in range(n)]
        return f"({', '.join(params)})->{self.type(ret_t)}"


def main():
    mode = sys.argv[1]
    z = zipfile.ZipFile(APK)
    dex_names = sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
    for dn in dex_names:
        dx = Dex(z.read(dn))
        if mode == 'sig':
            ret = sys.argv[2]
            params = sys.argv[3:]
            want = f"({', '.join(params)})->{ret}"
            hits = [(i, c, p, n) for i, c, p, n in dx.method_ids() if p == want]
            print(f'{dn}: {len(hits)} method_ids with {want}')
            for i, c, p, n in hits:
                print(f'  mid={i} {c}.{n} {p}')
        elif mode == 'name':
            nm = sys.argv[2]
            hits = [(i, c, p, n) for i, c, p, n in dx.method_ids() if n == nm]
            print(f'{dn}: {len(hits)} method_ids named {nm}')
            for i, c, p, n in hits:
                print(f'  mid={i} {c}.{n} {p}')


if __name__ == '__main__':
    main()
