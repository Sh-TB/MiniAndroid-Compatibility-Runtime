#!/usr/bin/env python3
"""cont11_xref.py — find all references to a target class across APK DEXes.
Usage: cont11_xref.py <apk> <Ldesc;>
Reports new-instance / const-class / check-cast / field / invoke sites with
the ENCLOSING class;method.
"""
import sys, zipfile, struct, io

apk = sys.argv[1]
target = sys.argv[2]

# explicit instruction sizes in 16-bit code units (Dalvik op table)
INS_SIZE = {}
for o in range(0x00, 0x12): INS_SIZE[o] = 1        # nop..move-object/16 misc
INS_SIZE[0x02] = 2; INS_SIZE[0x03] = 3             # move/from16, move/16
INS_SIZE[0x05] = 2; INS_SIZE[0x06] = 3
INS_SIZE[0x08] = 2; INS_SIZE[0x09] = 3
INS_SIZE[0x13] = 2  # const/16
INS_SIZE[0x14] = 3  # const
INS_SIZE[0x15] = 2  # const/high16
INS_SIZE[0x16] = 2  # const-wide/16
INS_SIZE[0x17] = 3  # const-wide/32
INS_SIZE[0x18] = 5  # const-wide
INS_SIZE[0x19] = 2  # const-wide/high16
INS_SIZE[0x1a] = 2  # const-string
INS_SIZE[0x1b] = 3  # const-string/jumbo
INS_SIZE[0x1c] = 2  # const-class
INS_SIZE[0x1f] = 2  # check-cast
INS_SIZE[0x20] = 2  # instance-of
INS_SIZE[0x22] = 2  # new-instance
INS_SIZE[0x23] = 2  # new-array
INS_SIZE[0x24] = 3  # filled-new-array
INS_SIZE[0x25] = 3  # filled-new-array/range
INS_SIZE[0x26] = 3  # fill-array-data
INS_SIZE[0x29] = 2  # goto/16
INS_SIZE[0x2a] = 3  # goto/32
INS_SIZE[0x2b] = 3  # packed-switch
INS_SIZE[0x2c] = 3  # sparse-switch
for o in range(0x2d, 0x32): INS_SIZE[o] = 2        # cmp ops
for o in range(0x32, 0x3e): INS_SIZE[o] = 2        # if-xx
for o in range(0x3e, 0x44): INS_SIZE[o] = 1        # unused
for o in range(0x44, 0x52): INS_SIZE[o] = 2        # aget/aput
for o in range(0x52, 0x6e): INS_SIZE[o] = 2        # iget/iput/sget/sput
for o in range(0x6e, 0x73): INS_SIZE[o] = 3        # invoke-*
INS_SIZE[0x73] = 1
for o in range(0x74, 0x79): INS_SIZE[o] = 3        # invoke-*/range
INS_SIZE[0x79] = 1; INS_SIZE[0x7a] = 1
for o in range(0x7b, 0x90): INS_SIZE[o] = 1        # unop
for o in range(0x90, 0xb0): INS_SIZE[o] = 2        # binop
for o in range(0xb0, 0xd0): INS_SIZE[o] = 1        # binop/2addr
for o in range(0xd0, 0xd8): INS_SIZE[o] = 2        # binop/lit16
for o in range(0xd8, 0xe3): INS_SIZE[o] = 2        # binop/lit8
for o in range(0xe3, 0xfa): INS_SIZE[o] = 1        # unused/special

INVOKE_NAMES = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
                0x71:'invoke-static',0x72:'invoke-interface',
                0x74:'invoke-virtual/range',0x75:'invoke-super/range',
                0x76:'invoke-direct/range',0x77:'invoke-static/range',
                0x78:'invoke-interface/range'}
FIELD_OPS = set(range(0x52, 0x6a))
TYPE_OPS = {0x1c:'const-class', 0x1f:'check-cast', 0x20:'instance-of', 0x22:'new-instance'}

def run_dex(dexname, data):
    def u4(off): return struct.unpack_from('<I', data, off)[0]
    def u2(off): return struct.unpack_from('<H', data, off)[0]
    string_ids_off = u4(0x3c); type_ids_off = u4(0x44)
    proto_ids_off = u4(0x4c); field_ids_off = u4(0x54)
    method_ids_off = u4(0x5c); class_defs_size = u4(0x60); class_defs_off = u4(0x64)

    def get_string(idx):
        off = u4(string_ids_off + 4*idx)
        n = 0; s = 0; p = off
        while True:
            b = data[p]; n |= (b & 0x7f) << s; s += 7; p += 1
            if not (b & 0x80): break
        raw = data[p:p+n]
        out = []; i = 0
        while i < len(raw):
            c = raw[i]
            if c == 0: break
            if c < 0x80: out.append(chr(c)); i += 1
            elif c < 0xe0: out.append(chr(((c & 0x1f) << 6) | (raw[i+1] & 0x3f))); i += 2
            else: out.append(chr(((c & 0x0f) << 12) | ((raw[i+1] & 0x3f) << 6) | (raw[i+2] & 0x3f))); i += 3
        return ''.join(out)

    def type_str(idx): return get_string(u4(type_ids_off + 4*idx))

    def method_info(idx):
        off = method_ids_off + 8*idx
        cls = type_str(u2(off)); proto = u2(off+2); name = get_string(u4(off+4))
        poff = proto_ids_off + 12*proto
        params_off = u4(poff+8)
        params = ''
        if params_off:
            for i in range(u4(params_off)):
                params += type_str(u2(params_off + 4 + 2*i))
        return cls, name, '(' + params + ')'

    def field_info(idx):
        off = field_ids_off + 8*idx
        return type_str(u2(off)), get_string(u4(off+4))

    out = []
    for ci in range(class_defs_size):
        coff = class_defs_off + 32*ci
        cls_desc = type_str(u4(coff))
        class_data_off = u4(coff + 24)
        if class_data_off == 0: continue
        p = class_data_off
        def uleb():
            nonlocal p
            r = 0; s = 0
            while True:
                b = data[p]; r |= (b & 0x7f) << s; s += 7; p += 1
                if not (b & 0x80): break
            return r
        sf = uleb(); iff = uleb(); dm = uleb(); vm = uleb()
        for _ in range(sf): uleb(); uleb()
        for _ in range(iff): uleb(); uleb()
        for kind, count in (('D', dm), ('V', vm)):
            midx = 0
            for _ in range(count):
                d = uleb(); midx += d >> 1
                code_off = uleb()
                if code_off == 0: continue
                mc, mn, md = method_info(midx)
                insns_size = u4(code_off + 12)
                insns_off = code_off + 16
                pc = 0
                while pc < insns_size:
                    unit = u2(insns_off + 2*pc)
                    op = unit & 0xff
                    # payload pseudo-ops
                    if op == 0x00:
                        hi = unit >> 8
                        if hi == 0x01:  # fill-array-data-payload
                            ew = u2(insns_off + 2*(pc+1))
                            size = u4(insns_off + 2*(pc+2))
                            pc += (8 + size * ew + 1) // 2
                            continue
                        if hi == 0x02:  # sparse-switch-payload
                            size = u2(insns_off + 2*(pc+1))
                            pc += 2 + 4 * size
                            continue
                        if hi == 0x03:  # packed-switch-payload
                            size = u2(insns_off + 2*(pc+1))
                            pc += 4 + 2 * size
                            continue
                    sz = INS_SIZE.get(op, 1)
                    detail = None
                    if op in TYPE_OPS:
                        t = type_str(u2(insns_off + 2*(pc+1)))
                        if t == target: detail = f'{TYPE_OPS[op]} {t}'
                    elif op in FIELD_OPS:
                        fc, fn = field_info(u2(insns_off + 2*(pc+1)))
                        if fc == target: detail = f'field {fc}.{fn}'
                    elif op in INVOKE_NAMES:
                        mc2, mn2, md2 = method_info(u2(insns_off + 2*(pc+1)))
                        if mc2 == target:
                            detail = f'{INVOKE_NAMES[op]} {mc2}-> {mn2}{md2}'
                    if detail:
                        out.append((cls_desc, f'{mn}{md}', hex(pc*2), detail))
                    pc += sz
    return out

zf = zipfile.ZipFile(apk)
total = 0
for dn in sorted(n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')):
    for cls_desc, meth, at, detail in run_dex(dn, zf.read(dn)):
        print(f'{dn} {cls_desc}-> {meth}  @{at}  {detail}')
        total += 1
print('TOTAL', total)
