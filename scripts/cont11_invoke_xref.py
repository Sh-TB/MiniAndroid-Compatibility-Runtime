#!/usr/bin/env python3
"""CONT-11: find every method that invokes methods matching a pattern
(e.g. 'Landroid/graphics/Canvas;.draw' or 'Ljt1;.draw') across all DEX
classes of an APK. Read-only evidence tool.
Usage: cont11_invoke_xref.py <apk> <invoke-target-substring>"""
import sys, zipfile, struct

SIZES = {}
def build_sizes():
    T = {}
    for op in range(0x00, 0x10): T[op] = {0x00:1,0x01:1,0x02:1,0x03:1,0x04:1,0x05:2,0x06:2,0x07:2,0x08:1,0x09:2,0x0a:1,0x0b:1,0x0c:1,0x0d:1,0x0e:1,0x0f:1}.get(op,1)
    T.update({0x10:1,0x11:1,0x12:1,0x13:2,0x14:3,0x15:2,0x16:2,0x17:3,0x18:5,0x19:2,0x1a:2,0x1b:3,0x1c:2})
    for op in range(0x1d, 0x32): T[op] = 1
    for op in range(0x32, 0x3e): T[op] = 2
    for op in range(0x3e, 0x44): T[op] = 2
    for op in range(0x44, 0x60): T[op] = 2
    for op in range(0x60, 0x6e): T[op] = 2
    T[0x6e] = 3; T[0x6f] = 3; T[0x70] = 3; T[0x71] = 3; T[0x72] = 3
    T[0x74] = 4; T[0x75] = 4; T[0x76] = 4; T[0x77] = 4; T[0x78] = 4
    for op in range(0x7b, 0x90): T[op] = 1
    for op in range(0x90, 0xb0): T[op] = 2
    for op in range(0xb0, 0xd0): T[op] = 1
    for op in range(0xd0, 0xd8): T[op] = 2
    for op in range(0xd8, 0xe3): T[op] = 2
    T[0xe3] = 3
    for op in range(0xe4, 0xfa): T[op] = 1
    T[0xfa] = 3; T[0xfb] = 3; T[0xfc] = 2; T[0xfd] = 2; T[0xfe] = 1; T[0xff] = 1
    SIZES.update(T)
INVOKE_OPS = {0x6e:'virtual',0x6f:'super',0x70:'direct',0x71:'static',0x72:'interface',0x74:'virtual/range',0x75:'super/range',0x76:'direct/range',0x77:'static/range',0x78:'interface/range'}

def uleb(data, p):
    r = 0; sh = 0
    while True:
        b = data[p]; p += 1
        r |= (b & 0x7f) << sh
        if not (b & 0x80): break
        sh += 7
    return r, p

def main():
    build_sizes()
    apk, pat = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(apk)
    for name in sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')):
        data = z.read(name)
        if data[:4] != b'dex\n': continue
        string_ids_size, string_ids_off = struct.unpack_from('<II', data, 56)
        type_ids_size, type_ids_off = struct.unpack_from('<II', data, 64)
        field_ids_size, field_ids_off = struct.unpack_from('<II', data, 80)
        method_ids_size, method_ids_off = struct.unpack_from('<II', data, 88)
        cd_size, cd_off = struct.unpack_from('<II', data, 96)
        strings = []
        for i in range(string_ids_size):
            (soff,) = struct.unpack_from('<I', data, string_ids_off + i*4)
            _, p = uleb(data, soff)
            end = data.index(b'\x00', p)
            strings.append(data[p:end].decode('utf-8','replace'))
        types = []
        for i in range(type_ids_size):
            (si,) = struct.unpack_from('<I', data, type_ids_off + i*4)
            types.append(strings[si])
        mcls, mnm = [], []
        for i in range(method_ids_size):
            ci, pi, ni = struct.unpack_from('<HHI', data, method_ids_off + i*8)
            mcls.append(types[ci]); mnm.append(strings[ni])
        hits = []
        for ci in range(cd_size):
            cdo = cd_off + ci * 32
            class_idx = struct.unpack_from('<I', data, cdo)[0]
            cdata_off = struct.unpack_from('<I', data, cdo + 24)[0]
            if cdata_off == 0: continue
            this_cls = types[class_idx]
            p = cdata_off
            sf, p = uleb(data, p); inf, p = uleb(data, p); dm, p = uleb(data, p); vm, p = uleb(data, p)
            fid = 0
            for _ in range(sf):
                d, p = uleb(data, p); fid += d
                _, p = uleb(data, p)  # access_flags
            for _ in range(inf):
                d, p = uleb(data, p); fid += d
                _, p = uleb(data, p)  # access_flags
            for kind, cnt in (('D', dm), ('V', vm)):
                mid = 0  # delta sequence RESTARTS per array (per cont9_dexdump law)
                for _ in range(cnt):
                    d, p = uleb(data, p); mid += d
                    acc, p = uleb(data, p)
                    coff, p = uleb(data, p)
                    if coff == 0: continue
                    mname_idx = struct.unpack_from('<I', data, method_ids_off + mid*8 + 4)[0]
                    if mname_idx >= len(strings):
                        print(f"  !! OOB name_idx={mname_idx} mid={mid} class={this_cls} method_ids_size={method_ids_size}", file=sys.stderr)
                        continue
                    mname = strings[mname_idx]
                    reg, ins, outs, tries, dbg, isz = struct.unpack_from('<HHHHII', data, coff)
                    ip = coff + 16
                    end = ip + isz*2
                    found = []
                    while ip < end:
                        w = struct.unpack_from('<H', data, ip)[0]
                        op = w & 0xff
                        if op == 0x00 and w == 0x0100:  # packed-switch-payload
                            sz2 = struct.unpack_from('<H', data, ip+2)[0]
                            ip += 8 + sz2*2
                            continue
                        if op == 0x00 and w == 0x0200:  # sparse-switch-payload
                            sz2 = struct.unpack_from('<H', data, ip+2)[0]
                            ip += 4 + sz2*8
                            continue
                        if op == 0x00 and w == 0x0300:  # fill-array-data-payload
                            ew = struct.unpack_from('<H', data, ip+2)[0]
                            sz3 = struct.unpack_from('<I', data, ip+4)[0]
                            nbytes = 8 + ew*sz3
                            ip += nbytes + (nbytes & 1)
                            continue
                        if op in INVOKE_OPS:
                            (midw,) = struct.unpack_from('<H', data, ip+2)
                            if midw < len(mcls):
                                ref = f"{mcls[midw]}.{mnm[midw]}"
                                if pat in ref:
                                    found.append(f"pc={ip-coff-16:#x} {INVOKE_OPS[op]} {ref}")
                        ip += SIZES.get(op, 1) * 2
                    if found:
                        hits.append((this_cls, mname, kind, found))
        print(f"== {name}: {len(hits)} methods invoking ~{pat}~")
        for cls, mname, kind, found in hits:
            print(f"  {cls}.{mname} [{kind}]")
            for f in found[:6]:
                print(f"     {f}")

if __name__ == '__main__':
    main()
