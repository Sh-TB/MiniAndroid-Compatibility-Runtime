#!/usr/bin/env python3
"""cont159_disasm.py — tower3d decode: disassemble methods from an APK's dex.
Usage: cont159_disasm.py <apk> <class-desc-with-semicolon> <method-name> [method-name2 ...]
Prints instructions with pc offsets for the named method(s)."""
import struct, zipfile, sys

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

def main():
    apk = sys.argv[1]
    cls = sys.argv[2]            # e.g. Lcom/badlogic/gdx/utils/Array;
    names = set(sys.argv[3:])
    zf = zipfile.ZipFile(apk)
    dex_names = [n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')]
    d = None
    for dn in dex_names:
        data = zf.read(dn)
        str_size, str_off = struct.unpack_from('<2I', data, 0x38)
        soa = struct.unpack_from(f'<{str_size}I', data, str_off)
        def str_at(si, d=data, soa=soa):
            off = soa[si]; _, o = uleb(d, off)
            return d[o:d.index(b'\x00', o)].decode('utf-8', 'replace')
        type_size, type_off = struct.unpack_from('<2I', data, 0x40)
        toa = struct.unpack_from(f'<{type_size}I', data, type_off)
        def type_at(ti, d=data, toa=toa):
            return str_at(toa[ti], d, soa)
        # find class def
        class_size, class_off = struct.unpack_from('<2I', data, 0x60)
        found = None
        for i in range(class_size):
            off = class_off + i * 32
            cidx = struct.unpack_from('<I', data, off)[0]
            if type_at(cidx, data, toa) == cls:
                found = (i, off, data)
                break
        if not found:
            continue
        _, coff, d = found
        str_size2, str_off2 = struct.unpack_from('<2I', d, 0x38)
        soa2 = struct.unpack_from(f'<{str_size2}I', d, str_off2)
        type_size2, type_off2 = struct.unpack_from('<2I', d, 0x40)
        toa2 = struct.unpack_from(f'<{type_size2}I', d, type_off2)
        proto_size, proto_off = struct.unpack_from('<2I', d, 0x48)
        foa_size, foa_off = struct.unpack_from('<2I', d, 0x50)
        moa_size, moa_off = struct.unpack_from('<2I', d, 0x58)
        def str_at2(si, d=d, soa2=soa2):
            off = soa2[si]; _, o = uleb(d, off)
            return d[o:d.index(b'\x00', o)].decode('utf-8', 'replace')
        def type_at2(ti, d=d, toa2=toa2):
            return str_at2(toa2[ti], d, soa2)
        def proto_at(pi, d=d, proto_off=proto_off):
            so, rt, po = struct.unpack_from('<3I', d, proto_off + pi * 12)
            shorty = str_at2(so, d, soa2)
            params_off = uleb(d, po)[0] if po else 0
            n = uleb(d, params_off)[0] if params_off else 0
            pts = [type_at2(struct.unpack_from('<H', d, params_off + 2 + 2*i)[0], d, toa2) for i in range(n)] if params_off else []
            return shorty, type_at2(rt, d, toa2), pts
        def meth_at(mi, d=d, moa_off=moa_off):
            m = struct.unpack_from('<I', d, moa_off + mi * 8 + 4)[0]
            return str_at2(m, d, soa2)
        print(f'class {cls} found (dex {dn})')
        class_data_off = struct.unpack_from('<I', d, coff + 24)[0]
        if not class_data_off:
            print('  (no class_data)')
            return
        o = class_data_off
        sf, inf, dm, vm = [uleb(d, o + i)[0] for i in range(4)]
        # advance past all ulebs properly
        o = class_data_off
        vals = []
        for _ in range(4):
            v, o = uleb(d, o); vals.append(v)
        sf, inf, dm, vm = vals
        # static fields
        fi = 0
        for _ in range(sf):
            _, o = uleb(d, o); _, o = uleb(d, o); fi += 1
        for _ in range(inf):
            _, o = uleb(d, o); _, o = uleb(d, o)
        for mi in range(dm):
            miidx, o = uleb(d, o); acc, o = uleb(d, o); code_off = uleb(d, o)[0]
            midx = fi + miidx
            mname = meth_at(midx, d, moa_off)
            if mname in names:
                dump_method(d, code_off, mname, str_at2, type_at2, proto_at, moa_off)
        for mi in range(vm):
            miidx, o = uleb(d, o); acc, o = uleb(d, o); code_off = uleb(d, o)[0]
            midx = fi + dm + miidx
            mname = meth_at(midx, d, moa_off)
            if mname in names:
                dump_method(d, code_off, mname, str_at2, type_at2, proto_at, moa_off)
        return
    print(f'class {cls} NOT FOUND in {apk}')

def dump_method(d, code_off, mname, str_at, type_at, proto_at, moa_off):
    reg_sz, ins_sz, outs_sz, tries_sz, dbg_off, insns_sz = struct.unpack_from('<6H', d, code_off)
    print(f'--- {mname} (code_off={code_off:#x} regs={reg_sz} ins={ins_sz} outs={outs_sz} insns={insns_sz})')
    base = code_off + 16
    pc = 0
    idx = 0
    insns = struct.unpack_from(f'<{insns_sz}H', d, base)
    while idx < insns_sz:
        w = insns[idx]
        op = w & 0xFF
        extra = ''
        # common formats: 10x, 12x, 11n, 11x, 10t, 20t, 22x, 21t, 21s, 21h, 21c, 23x, 30t, 31i, 31t, 31c, 32x, 35c, 3rc, 51l
        width = 1
        if op == 0x00:
            nop = w >> 8
            if nop == 0x0100 or nop == 0x0200 or nop == 0x0300:
                size = nop >> 8
                width = size if size else 2  # packed-switch payload etc. simplified
        elif op in (0x01, 0x07, 0x08, 0x0a): width = 1   # move et al 12x
        elif op in (0x02, 0x03, 0x04, 0x05, 0x06, 0x09, 0x0b, 0x0c, 0x0d): width = 2  # 22x/32x
        elif op == 0x0e: width = 1  # return-void
        elif op in (0x0f, 0x10, 0x11, 0x12, 0x1d, 0x1e, 0x27, 0x28): width = 1
        elif op in (0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1f, 0x20, 0x22): width = 2
        elif op in (0x21, 0x23, 0x24, 0x25, 0x26): width = 2
        elif op in (0x29, 0x2a):  # sparse/packed switch
            width = 3
        elif op in (0x2b, 0x2c):
            width = 3
        elif 0x2d <= op <= 0x31: width = 2  # cmp
        elif 0x32 <= op <= 0x37: width = 2  # if-test t
        elif 0x38 <= op <= 0x3d: width = 2  # if-test z
        elif 0x3e <= op <= 0x43: width = 1
        elif 0x44 <= op <= 0x51: width = 2  # aget/aput
        elif 0x52 <= op <= 0x5f: width = 2  # iget/iput
        elif 0x60 <= op <= 0x6d: width = 2  # sget/sput
        elif 0x6e <= op <= 0x72: width = 3  # invoke-kind 35c
        elif op in (0x74, 0x75, 0x76, 0x77, 0x78): width = 3  # invoke-kind/range
        elif 0x79 <= op <= 0x7a: width = 1
        elif 0x7b <= op <= 0x8f: width = 1  # unop
        elif 0x90 <= op <= 0xaf: width = 2  # binop
        elif 0xb0 <= op <= 0xcf: width = 1  # binop/2addr
        elif 0xd0 <= op <= 0xd7: width = 2  # binop/lit16
        elif 0xd8 <= op <= 0xe2: width = 2  # binop/lit8
        else: width = 1
        # resolve index for 21c/22c/31c/35c/45cc etc: second unit for width>=2 has index
        if op in (0x1a, 0x1b, 0x1c, 0x20, 0x22) or 0x52 <= op <= 0x6d:
            if idx + 1 < insns_sz:
                iidx = insns[idx + 1]
                if 0x52 <= op <= 0x5f or 0x60 <= op <= 0x6d:  # field
                    foff = struct.unpack_from('<I', d, 0)[0]  # placeholder
                    extra = f'field@{iidx:#x}'
                else:
                    extra = f'str/type@{iidx:#x}'
        if 0x6e <= op <= 0x78:
            if idx + 2 < insns_sz:
                mref = insns[idx + 2]
                extra = f'method@{mref:#x}'
                # method_id: u2 class, u2 proto, u4 name
                mcls, mproto, mname_i = struct.unpack_from('<HHI', d, moa_off + mref * 8)
                try:
                    extra += f' -> {type_at2(mcls)}->{str_at2(mname_i)}'
                except Exception:
                    pass
        if op == 0x22 and idx + 1 < insns_sz:
            tref = insns[idx + 1]
            try:
                extra = f'type {type_at(tref)}'
            except Exception:
                pass
        print(f'  pc={pc:4d} {insns[idx]:04x} op={op:#04x} {extra}')
        idx += width
        pc += width * 2

if __name__ == '__main__':
    main()
