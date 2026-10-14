#!/usr/bin/env python3
"""CONT-11: find every method that reads/writes a given STATIC field
(cls;.name) across all DEX classes of an APK. Read-only evidence tool.
Usage: cont11_static_field_xref.py <apk> <Lcls;> <fieldname>"""
import sys, zipfile, struct

def uleb(data, p):
    r = 0; sh = 0
    while True:
        b = data[p]; p += 1
        r |= (b & 0x7f) << sh
        if not (b & 0x80): break
        sh += 7
    return r, p

def main():
    apk, cls, fld = sys.argv[1], sys.argv[2], sys.argv[3]
    z = zipfile.ZipFile(apk)
    for name in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
        data = z.read(name)
        if data[:4] != b'dex\n': continue
        # header tables
        string_ids_size, string_ids_off = struct.unpack_from('<II', data, 56)
        type_ids_size, type_ids_off = struct.unpack_from('<II', data, 64)
        proto_off = struct.unpack_from('<I', data, 76)[0]
        field_ids_size, field_ids_off = struct.unpack_from('<II', data, 80)
        method_ids_size, method_ids_off = struct.unpack_from('<II', data, 88)
        # strings
        strings = []
        for i in range(string_ids_size):
            (soff,) = struct.unpack_from('<I', data, string_ids_off + i*4)
            _, p = uleb(data, soff)
            end = data.index(b'\x00', p)
            strings.append(data[p:end].decode('utf-8','replace'))
        # types
        types = []
        for i in range(type_ids_size):
            (si,) = struct.unpack_from('<I', data, type_ids_off + i*4)
            types.append(strings[si])
        # fields
        fcls, fty, fnm = [], [], []
        target_fid = None
        for i in range(field_ids_size):
            ci, ti, ni = struct.unpack_from('<HHI', data, field_ids_off + i*8)
            c, t, n = types[ci], types[ti], strings[ni]
            fcls.append(c); fty.append(t); fnm.append(n)
            if c == cls and n == fld:
                target_fid = i
        if target_fid is None:
            print(f"{name}: field {cls}.{fld} NOT FOUND"); continue
        print(f"== {name}: {cls}.{fld}:{fty[target_fid]} field_id={target_fid}")
        # walk class_defs -> class_data for methods
        cd_size, cd_off = struct.unpack_from('<II', data, 96)
        for ci in range(cd_size):
            cdo = cd_off + ci * 32
            class_idx, access, super_idx, ifaces_off, src, ant, cdata_off = struct.unpack_from('<IIIII II'.replace(' ',''), data, cdo)
            if cdata_off == 0: continue
            this_cls = types[class_idx]
            p = cdata_off
            sf, inf, dm, vm = [uleb(data, p)[0] for _ in range(4)] if False else (None,)*4
            sf, p = uleb(data, p); inf, p = uleb(data, p); dm, p = uleb(data, p); vm, p = uleb(data, p)
            # skip static + instance fields
            fid = 0
            for _ in range(sf):
                d, p = uleb(data, p); fid += d
            for _ in range(inf):
                d, p = uleb(data, p); fid += d
            def skip_codes(p, n):
                for _ in range(n):
                    d, p = uleb(data, p)
                return p
            p = skip_codes(p, dm)
            mid = 0
            for _ in range(vm):
                d, p = uleb(data, p); mid += d
            # now direct+virtual with code offsets need full parse; easier: re-parse with code_item capture
            # restart class_data parse capturing methods
            p = cdata_off
            sf, p = uleb(data, p); inf, p = uleb(data, p); dm, p = uleb(data, p); vm, p = uleb(data, p)
            fid = 0
            for _ in range(sf):
                d, p = uleb(data, p); fid += d
            for _ in range(inf):
                d, p = uleb(data, p); fid += d
            methods = []
            for kind, cnt in (('D', dm), ('V', vm)):
                mid = 0
                for _ in range(cnt):
                    d, p = uleb(data, p); mid += d
                    acc, p = uleb(data, p)
                    methods.append((kind, mid, acc, p))
            # code offsets are stored AFTER all encoded_method entries in a code array? No:
            # encoded_method = method_idx_diff, access_flags, code_off (3 ulebs)
            # re-parse properly:
            p = cdata_off
            sf, p = uleb(data, p); inf, p = uleb(data, p); dm, p = uleb(data, p); vm, p = uleb(data, p)
            fid = 0
            for _ in range(sf):
                d, p = uleb(data, p); fid += d
            for _ in range(inf):
                d, p = uleb(data, p); fid += d
            for kind, cnt in (('D', dm), ('V', vm)):
                mid = 0
                for _ in range(cnt):
                    d, p = uleb(data, p); mid += d
                    acc, p = uleb(data, p)
                    coff, p = uleb(data, p)
                    if coff == 0: continue
                    mname_idx, mproto_idx = struct.unpack_from('<HH', data, method_ids_off + mid*8)
                    mname = strings[mname_idx]
                    reg, ins, outs, tries, dbg, isz = struct.unpack_from('<HHHHII', data, coff)
                    ip = coff + 16
                    end = ip + isz*2
                    while ip < end:
                        w = struct.unpack_from('<H', data, ip)[0]
                        op = w & 0xff
                        # scan for sput/sget-object on target: opcodes 0x62 sget-object, 0x69 sput-object, 0x6a sput-object? actual: 0x62=sget-object,0x69=sput,0x6a=sput-object? use table:
                        # 61 sget-short? Let me use: 0x60 sget,0x61 sget-wide,0x62 sget-object,0x63 sget-boolean,0x64 sget-byte,0x65 sget-char,0x66 sget-short
                        # 0x67 sput,0x68 sput-wide,0x69 sput-object,0x6a sput-boolean,0x6b sput-byte,0x6c sput-char,0x6d sput-short
                        if op in (0x62, 0x69):
                            (fidw,) = struct.unpack_from('<H', data, ip+2)
                            if fidw == target_fid:
                                rw = 'READ' if op == 0x62 else 'WRITE'
                                print(f"  {this_cls}.{mname} {kind} pc={ip-coff-16:#x} {rw}")
                        sz = [2,2,2,2,2,2,2,2,2,3,3,2,2,3,3,3,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2][op] if op < 0x20 else None
                        if sz is None:
                            # standard sizes
                            T = {0x00:1,0x01:1,0x02:1,0x03:1,0x04:1,0x05:2,0x06:2,0x07:2,0x08:1,0x09:2,0x0a:1,0x0b:1,0x0c:1,0x0d:1,0x0e:1,0x0f:1,0x10:1,0x11:1,0x12:1,0x13:2,0x14:3,0x15:2,0x16:2,0x17:3,0x18:5,0x19:2,0x1a:2,0x1b:3,0x1c:2}
                            sz = T.get(op)
                            if sz is None:
                                if 0x1d <= op <= 0x31: sz = 2
                                elif op in (0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39): sz = 2
                                elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78,0x79,0x7a): sz = 2 if op < 0x74 or op in (0x74,0x75,0x76,0x77,0x78) and False else (3 if op in (0x74,0x75,0x76,0x77,0x78) else 2)
                                elif op in (0x73,0x79,0x7a): sz = 1
                                elif 0x7b <= op <= 0x8f: sz = 1
                                elif 0x90 <= op <= 0xaf: sz = 2
                                elif 0xb0 <= op <= 0xcf: sz = 1
                                elif 0xd0 <= op <= 0xd7: sz = 2
                                elif op in (0xd8,0xd9,0xda,0xdb,0xdc,0xdd,0xde,0xdf,0xe0,0xe1,0xe2): sz = 2
                                elif op == 0xe3: sz = 3
                                elif op == 0xfa: sz = 3
                                elif op == 0xfb: sz = 3
                                elif op == 0xfc: sz = 2
                                elif op == 0xfd: sz = 2
                                elif op == 0xfe: sz = 1
                                elif op == 0xff: sz = 1
                                else: sz = 1
                        ip += sz*2 if sz >= 1 else 2
    return

if __name__ == '__main__':
    main()
