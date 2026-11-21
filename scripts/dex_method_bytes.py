#!/usr/bin/env python3
"""Dump one method's code bytes + decoded const-string refs (dex, minimal)."""
import struct, sys, zipfile

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if b < 0x80: return r, off
        s += 7

def main(apk, cls_want, meth_want):
    z = zipfile.ZipFile(apk)
    d = z.read([n for n in z.namelist() if n.endswith('.dex')][0])
    sids_size, = struct.unpack_from('<I', d, 0x38); sids_off, = struct.unpack_from('<I', d, 0x3c)
    tids_off, = struct.unpack_from('<I', d, 0x44)
    mids_off, = struct.unpack_from('<I', d, 0x5c)
    cdefs_size, = struct.unpack_from('<I', d, 0x60); cdefs_off, = struct.unpack_from('<I', d, 0x64)

    def get_str(i):
        off, = struct.unpack_from('<I', d, sids_off + i * 4)
        n, off = uleb(d, off)
        return d[off:off + n].decode('utf-8', 'replace')
    def get_type(i):
        si, = struct.unpack_from('<I', d, tids_off + i * 4)
        return get_str(si)

    target = 'L' + cls_want.replace('.', '/') + ';'
    for i in range(cdefs_size):
        p = cdefs_off + i * 32
        if get_type(struct.unpack_from('<I', d, p)[0]) != target: continue
        cdo, = struct.unpack_from('<I', d, p + 24)
        if cdo == 0:
            continue
        off = cdo
        sf, off = uleb(d, off); inf, off = uleb(d, off)
        dm, off = uleb(d, off); vm, off = uleb(d, off)
        print(f'# counts: static_f={sf} inst_f={inf} direct={dm} virtual={vm} cdo={cdo}')
        for _ in range(sf + inf): _, off = uleb(d, off); _, off = uleb(d, off)
        idx = 0
        for sec, cnt in (('direct', dm), ('virtual', vm)):
            for k in range(cnt):
                dif, off = uleb(d, off); idx += dif
                _, off = uleb(d, off)
                code_off, off = uleb(d, off)
                print(f'# m[{sec} {k}] idx={idx} code_off={code_off} (file={len(d)})', file=sys.stderr)
                p2 = mids_off + idx * 8  # runtime DexMethodId model (dex_parser.h:96)
                name = get_str(struct.unpack_from('<I', d, p2 + 4)[0])
                if name != meth_want: continue
                if code_off == 0:
                    print(f'{name}: abstract/native'); return
                regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<6H', d, code_off + 4)[:6]
                # code_item header: registers_size u16, ins u16, outs u16, tries u16,
                # debug_info_off u32, insns_size u32
                insns_size, = struct.unpack_from('<I', d, code_off + 12)
                base = code_off + 16
                print(f'{name}: regs={regs} insns_size={insns_size} (16-bit units)')
                codes = d[base:base + insns_size * 2]
                words = struct.unpack(f'<{insns_size}H', codes)
                pc = 0
                while pc < insns_size:
                    op = words[pc] & 0xff
                    if op in (0x1a, 0x1b):  # const-string, const-string/jumbo
                        try:
                            if op == 0x1a:
                                sidx = (words[pc] >> 8) & 0xff
                                print(f'  pc{pc:04x}: const-string s#{sidx} = "{get_str(sidx)[:80]}"')
                                pc += 1
                            else:
                                sidx = words[pc + 1] | (words[pc + 2] << 16)
                                print(f'  pc{pc:04x}: const-string/jumbo s#{sidx} = "{get_str(sidx)[:80]}"')
                                pc += 3
                        except Exception:
                            print(f'  pc{pc:04x}: const-string <unreadable>'); pc += 2 if op == 0x1a else 3
                    elif op == 0x22:  # new-instance
                        ti = words[pc + 1]
                        print(f'  pc{pc:04x}: new-instance {get_type(ti)}')
                        pc += 2
                    elif op == 0x27:
                        print(f'  pc{pc:04x}: throw')
                        pc += 1
                    elif op in (0x1c, 0x1f):
                        ti = words[pc + 1]
                        print(f'  pc{pc:04x}: {"const-class" if op==0x1c else "check-cast"} {get_type(ti)}')
                        pc += 2
                    else:
                        pc += 1
                return
    print('not found')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
