#!/usr/bin/env python3
"""S216 CONT-132 — disassemble Lbw0;.a and Lbw0;.d from the canonical dooz APK.
Ground truth for the wild-index aput: which instruction feeds the index
register at pc=8 of .a, and which return sites .d has."""
import struct, zipfile

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
WANT = {("Lbw0;", "a"), ("Lbw0;", "d"), ("Lbw0;", "k"), ("Lbw0;", "f")}

z = zipfile.ZipFile(APK)
dex = z.read("classes.dex")


def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80):
            break
        s += 7
    return r, o


def sleb(b, o):
    r, o = uleb(b, o)
    # sign-extend
    sh = 32 - 0
    # recompute: uleb gives unsigned; re-encode sign from last byte
    return r, o


# parse header
string_ids_size, string_ids_off = struct.unpack_from("<II", dex, 0x38)
type_ids_size, type_ids_off = struct.unpack_from("<II", dex, 0x40)
proto_ids_size, proto_ids_off = struct.unpack_from("<II", dex, 0x48)
field_ids_size, field_ids_off = struct.unpack_from("<II", dex, 0x50)
method_ids_size, method_ids_off = struct.unpack_from("<II", dex, 0x58)
class_defs_size, class_defs_off = struct.unpack_from("<II", dex, 0x60)


def get_string(idx):
    off = struct.unpack_from("<I", dex, string_ids_off + 4 * idx)[0]
    n, off = uleb(dex, off)
    out = bytearray()
    for _ in range(n):
        c = dex[off]
        if c < 0x80:
            out.append(c); off += 1
        elif c >> 5 == 6:
            out.append(((c & 0x1F) << 6) | (dex[off + 1] & 0x3F)); off += 2
        else:
            out.append(((c & 0x0F) << 12) | ((dex[off + 1] & 0x3F) << 6)
                       | (dex[off + 2] & 0x3F)); off += 3
    return out.decode("utf-8", "replace")


def get_type(idx):
    sidx = struct.unpack_from("<I", dex, type_ids_off + 4 * idx)[0]
    return get_string(sidx)


def get_method(idx):
    off = method_ids_off + 8 * idx
    cls, proto, name = struct.unpack_from("<HHI", dex, off)
    return get_type(cls), get_string(name)


OPSIZE = {}
for i in range(256):
    OPSIZE[i] = 1
for op in (0x04,0x05,0x06,0x07): OPSIZE[op]=2
OPSIZE[0x13]=2; OPSIZE[0x15]=2; OPSIZE[0x16]=2; OPSIZE[0x19]=2
OPSIZE[0x1a]=2; OPSIZE[0x1d]=1; OPSIZE[0x14]=3; OPSIZE[0x17]=3; OPSIZE[0x18]=5
OPSIZE[0x1b]=3
for op in (0x20,0x21,0x22,0x23): OPSIZE[op]=2
for op in (0x24,0x25,0x26,0x27): OPSIZE[op]=3
for op in range(0x28,0x2d): OPSIZE[op]=1
for op in range(0x2d,0x32): OPSIZE[op]=2
for op in range(0x32,0x38): OPSIZE[op]=2
for op in range(0x38,0x3d): OPSIZE[op]=2
for op in range(0x3d,0x42): OPSIZE[op]=2
for op in range(0x44,0x53): OPSIZE[op]=3
for op in range(0x52,0x5c): OPSIZE[op]=2
for op in range(0x5c,0x62): OPSIZE[op]=1
for op in range(0x62,0x6e): OPSIZE[op]=1
for op in range(0x6e,0x72): OPSIZE[op]=3
for op in range(0x74,0x79): OPSIZE[op]=3
for op in range(0x7b,0x90): OPSIZE[op]=1
for op in range(0x90,0xb0): OPSIZE[op]=3
for op in range(0xb0,0xd0): OPSIZE[op]=1
for op in range(0xd0,0xd8): OPSIZE[op]=2
for op in range(0xd8,0xe3): OPSIZE[op]=2
for op in (0xe3,0xe4,0xe5,0xe6,0xe7,0xe8,0xe9,0xea,0xeb,0xec,0xed,0xee,0xef,0xfa):
    OPSIZE[op]=2 if op==0xfa else 1
OPSIZE[0xfb]=2; OPSIZE[0xfc]=2; OPSIZE[0xfd]=2; OPSIZE[0xfe]=1; OPSIZE[0xff]=1
# fix known sizes per dalvik spec
OPSIZE[0x01]=1; OPSIZE[0x02]=1; OPSIZE[0x03]=1
OPSIZE[0x08]=1; OPSIZE[0x09]=1; OPSIZE[0x0a]=1; OPSIZE[0x0b]=1
OPSIZE[0x0c]=1; OPSIZE[0x0d]=1; OPSIZE[0x0e]=1; OPSIZE[0x0f]=1
OPSIZE[0x10]=1; OPSIZE[0x11]=1; OPSIZE[0x12]=1
OPSIZE[0x1c]=1; OPSIZE[0x1f]=2
OPSIZE[0x2b]=3; OPSIZE[0x2c]=3
OPSIZE[0x72]=3; OPSIZE[0x73]=3; OPSIZE[0x78]=3
OPSIZE[0x90]=1
# 51l pseudo
OPSIZE[0x18]=5

OPNAMES = {
 0x00:'nop',0x01:'move',0x02:'move/from16',0x04:'move-wide',0x05:'move-wide/from16',
 0x07:'move-object',0x08:'move-object/from16',0x0e:'return-void',0x0f:'return',
 0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',
 0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',
 0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',
 0x1b:'const-string/jumbo',0x1c:'const-class',0x1f:'check-cast',
 0x20:'instance-of',0x21:'array-length',0x22:'new-instance',0x23:'new-array',
 0x24:'filled-new-array',0x25:'filled-new-array/range',0x26:'fill-array-data',
 0x27:'throw',0x28:'goto',0x29:'goto/16',0x2b:'goto/32',0x2c:'packed-switch',
 0x2d:'sparse-switch',0x2e:'cmpl-float',0x31:'cmpg-double',0x32:'if-eq',
 0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
 0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',
 0x3d:'if-lez',0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',
 0x48:'aget-byte',0x4b:'aget-short',0x4c:'aget-char',0x4d:'aput',0x4e:'aput-wide',
 0x4f:'aput-object',0x50:'aput-boolean',0x51:'aput-byte',0x54:'aput-short',
 0x55:'aput-char',0x56:'iget',0x57:'iget-wide',0x58:'iget-object',0x59:'iget-boolean',
 0x5a:'iget-byte',0x5b:'iget-char',0x5c:'iget-short',0x5d:'iput',0x5e:'iput-wide',
 0x5f:'iput-object',0x60:'iput-boolean',0x61:'iput-byte',0x62:'iput-short',
 0x63:'iput-char',0x64:'sget',0x65:'sget-wide',0x66:'sget-object',0x69:'sput',
 0x6a:'sput-wide',0x6b:'sput-object',0x6e:'invoke-virtual',0x6f:'invoke-super',
 0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
 0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
 0x77:'invoke-static/range',0x78:'invoke-interface/range',
 0x7b:'neg-int',0x7d:'int-to-int',0x7f:'int-to-byte',0x80:'int-to-char',
 0x81:'int-to-short',0x83:'int-to-long',0x84:'long-to-int',0x85:'long-to-float',
 0x86:'long-to-double',0x88:'float-to-int',0x89:'float-to-long',
 0x8e:'double-to-int',0x8f:'double-to-long',0x90:'int-to-float',
 0x91:'int-to-double',0x92:'add-int',0x93:'sub-int',0x94:'mul-int',
 0x95:'div-int',0x96:'rem-int',0x97:'and-int',0x98:'or-int',0x99:'xor-int',
 0x9a:'shl-int',0x9b:'shr-int',0x9c:'ushr-int',0x9d:'add-long',0x9e:'sub-long',
 0x9f:'mul-long',0xa0:'div-long',0xa1:'rem-long',0xa2:'and-long',
 0xa3:'or-long',0xa4:'xor-long',0xa5:'shl-long',0xa6:'shr-long',
 0xa7:'ushr-long',0xa8:'add-float',0xa9:'sub-float',0xaa:'mul-float',
 0xab:'div-float',0xac:'rem-float',0xad:'add-double',0xae:'sub-double',
 0xaf:'mul-double',0xb0:'div-double',0xb1:'rem-double',
 0xb2:'add-int/2addr',0xb3:'sub-int/2addr',0xb4:'mul-int/2addr',
 0xb5:'div-int/2addr',0xb6:'rem-int/2addr',0xb7:'and-int/2addr',
 0xb8:'or-int/2addr',0xb9:'xor-int/2addr',0xba:'shl-int/2addr',
 0xbb:'shr-int/2addr',0xbc:'ushr-int/2addr',0xbd:'add-long/2addr',
 0xbe:'sub-long/2addr',0xbf:'mul-long/2addr',0xc0:'div-long/2addr',
 0xc1:'rem-long/2addr',0xc2:'and-long/2addr',0xc3:'or-long/2addr',
 0xc4:'xor-long/2addr',0xc5:'shl-long/2addr',0xc6:'shr-long/2addr',
 0xc7:'ushr-long/2addr',0xd0:'add-int/lit16',0xd1:'rsub-int',
 0xd2:'mul-int/lit16',0xd3:'div-int/lit16',0xd4:'rem-int/lit16',
 0xd5:'and-int/lit16',0xd6:'or-int/lit16',0xd7:'xor-int/lit16',
 0xd8:'add-int/lit8',0xd9:'rsub-int/lit8',0xda:'mul-int/lit8',
 0xdb:'div-int/lit8',0xdc:'rem-int/lit8',0xdd:'and-int/lit8',
 0xde:'or-int/lit8',0xdf:'xor-int/lit8',0xe0:'shl-int/lit8',
 0xe1:'shr-int/lit8',0xe2:'ushr-int/lit8',
}


def disasm_method(cls, name):
    # walk class defs
    for i in range(class_defs_size):
        off = class_defs_off + 32 * i
        cidx, = struct.unpack_from("<I", dex, off)
        if get_type(cidx) != cls:
            continue
        cfoff, = struct.unpack_from("<I", dex, off + 24)
        if cfoff == 0:
            continue
        ins_size, statics_size, _ = struct.unpack_from("<II", dex, cfoff + 4)[0:3] if False else (None,None,None)
        # class_data
        pos = cfoff
        static_fields_size, instance_fields_size, direct_methods_size, virtual_methods_size = struct.unpack_from("<IIII", dex, cfoff + 4)
        pos = cfoff + 16
        for _ in range(static_fields_size):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        for _ in range(instance_fields_size):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        for kind in (direct_methods_size, virtual_methods_size):
            midx_prev = 0
            for _ in range(kind):
                midx_delta, pos = uleb(dex, pos)
                flags, pos = uleb(dex, pos)
                code_off_delta, pos = uleb(dex, pos)
                midx_prev += midx_delta
                _, mname = get_method(midx_prev)
                if mname != name or code_off_delta == 0:
                    continue
                coff = code_off = prev_code  # placeholder
    return None


def walk_methods(cls):
    for i in range(class_defs_size):
        off = class_defs_off + 32 * i
        cidx, = struct.unpack_from("<I", dex, off)
        if get_type(cidx) != cls:
            continue
        cfoff, = struct.unpack_from("<I", dex, off + 24)
        if cfoff == 0:
            return
        s, ifc, dm, vm = struct.unpack_from("<IIII", dex, cfoff + 4)
        pos = cfoff + 16
        for _ in range(s):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        for _ in range(ifc):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        code = 0
        for kind in (dm, vm):
            midx = 0
            for _ in range(kind):
                d, pos = uleb(dex, pos)
                fl, pos = uleb(dex, pos)
                cd, pos = uleb(dex, pos)
                midx += d
                if cd:
                    code += cd
                _, mname = get_method(midx)
                if mname in ("a", "d", "k", "f") and cd:
                    yield mname, code
                    code = 0


# simpler: collect code offsets cumulatively per method
def method_code_offsets(cls):
    res = {}
    for i in range(class_defs_size):
        off = class_defs_off + 32 * i
        cidx, = struct.unpack_from("<I", dex, off)
        if get_type(cidx) != cls:
            continue
        cfoff, = struct.unpack_from("<I", dex, off + 24)
        if cfoff == 0:
            return res
        s, ifc, dm, vm = struct.unpack_from("<IIII", dex, cfoff + 4)
        pos = cfoff + 16
        for _ in range(s):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        for _ in range(ifc):
            _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
        acc = 0
        for kind in (dm, vm):
            midx = 0
            for _ in range(kind):
                d, pos = uleb(dex, pos)
                fl, pos = uleb(dex, pos)
                cd, pos = uleb(dex, pos)
                midx += d
                if cd:
                    acc += cd
                    _, mname = get_method(midx)
                    res[(cls, mname)] = acc
        return res
    return res


def disasm(coff):
    regs, ins = struct.unpack_from("<HH", dex, coff)
    units, = struct.unpack_from("<I", dex, coff + 12)
    body = coff + 16
    print(f"  registers={regs} ins={ins} code_units={units}")
    pc = 0
    out = []
    while pc < units:
        op = dex[body + 2 * pc]
        if op == 0x00:
            # nop or packed/sparse-switch pseudo or fill-array-data
            ident = struct.unpack_from("<H", dex, body + 2 * pc)[0]
            if ident == 0x0100:
                sz = struct.unpack_from("<I", dex, body + 2 * pc + 4)[0]
                n = sz * 2 + 4
                out.append((pc, f"fill-array-data payload ({sz} bytes)"))
                pc += 2 + n
                continue
            if ident == 0x0101 or ident == 0x0200 or ident == 0x0300:
                size = struct.unpack_from("<I", dex, body + 2 * pc + 2)[0]
                out.append((pc, "switch/payload"))
                pc += 2 + size * 2
                continue
            out.append((pc, "nop")); pc += 1; continue
        sz = OPSIZE.get(op, 1)
        raw = dex[body + 2 * pc: body + 2 * pc + 2 * sz]
        name = OPNAMES.get(op, f"op-{op:02x}")
        desc = name
        if op in (0x1a,):
            sidx = struct.unpack_from("<H", dex, body + 2 * pc + 2)[0]
            desc = f"const-string v{raw[1]}, \"{get_string(sidx)[:20]}\""
        elif op in (0x22, 0x1c, 0x1f, 0x20):
            tidx = struct.unpack_from("<H", dex, body + 2 * pc + 2)[0]
            desc = f"{name} .. {get_type(tidx)}"
        elif op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78):
            midx = struct.unpack_from("<H", dex, body + 2 * pc + 2)[0]
            c, n = get_method(midx)
            if op >= 0x74:
                r0 = raw[1]
                cnt = raw[5] >> 4
                desc = f"{name} {{{r0}..}} , {c}->{n} ({cnt} args)"
            else:
                extra = struct.unpack_from('<BBBB', dex, body+2*pc+4)[:nb] if nb>4 else ()
                regs_s = ','.join(str(x) for x in extra) if nb > 4 else \
                    ','.join(str(x) for x in raw[2:2+nb])
                desc = f"{name} ({nb}) [{regs_s}] {c}->{n}"
        elif op in (0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63):
            fidx = struct.unpack_from("<H", dex, body + 2 * pc + 2)[0]
            desc = f"{name} f#{fidx} v{raw[1]}, v{raw[3]}"
        elif op in (0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
            fidx = struct.unpack_from("<H", dex, body + 2 * pc + 2)[0]
            desc = f"{name} f#{fidx}"
        elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51,0x52,0x53):
            desc = f"{name} v{raw[1]}, v{raw[3]}, v{raw[5]}"
        elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
            tgt = struct.unpack_from('<h', dex, body + 2 * pc + 2)[0]
            desc = f"{name} v{raw[1]}, v{raw[3]} -> +{tgt}"
        elif 0x38 <= op <= 0x3d:
            tgt = struct.unpack_from('<h', dex, body + 2 * pc + 2)[0]
            desc = f"{name} v{raw[1]} -> +{tgt}"
        elif op in (0x28,):
            tgt = struct.unpack_from('<b', dex, body + 2 * pc + 1)[0]
            desc = f"goto -> +{tgt}"
        elif op in (0x29,):
            tgt = struct.unpack_from('<h', dex, body + 2 * pc + 2)[0]
            desc = f"goto/16 -> +{tgt}"
        elif op == 0x12:
            lit = raw[1] & 0xf
            sign = lit - 16 if lit > 7 else lit
            desc = f"const/4 v{(raw[1]>>4)&0xf}, {sign}"
        elif op == 0x13:
            v = struct.unpack_from('<h', dex, body + 2*pc+2)[0]
            desc = f"const/16 v{raw[1]}, {v}"
        elif op == 0x14:
            v = struct.unpack_from('<i', dex, body + 2*pc+2)[0]
            desc = f"const v{raw[1]}, {v} (0x{v&0xffffffff:08x})"
        elif op == 0x15:
            v = struct.unpack_from('<H', dex, body + 2*pc+2)[0] << 16
            desc = f"const/high16 v{raw[1]}, 0x{v:08x}"
        elif op in (0x92,0x93,0x94,0x95,0x96,0x97,0x98,0x99,0x9a,0x9b,0x9c,0x9d,0x9e,0x9f,0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7):
            desc = f"{name} v{raw[1]}, v{raw[3]}, v{raw[5]}"
        elif 0xb2 <= op <= 0xc7:
            desc = f"{name} v{raw[1]&0xf}, v{raw[1]>>4}"
        elif 0xd8 <= op <= 0xe2:
            lit = struct.unpack_from('<b', dex, body + 2*pc+3)[0]
            desc = f"{name} v{raw[1]&0xf}, v{raw[1]>>4}, {lit}"
        elif 0xd0 <= op <= 0xd7:
            lit = struct.unpack_from('<h', dex, body + 2*pc+2)[0]
            desc = f"{name} v{raw[1]&0xf}, v{raw[1]>>4}, {lit}"
        elif op in (0x7b,0x7c,0x7d,0x7e,0x7f,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,0x90,0x91):
            desc = f"{name} v{raw[1]&0xf}, v{raw[1]>>4}"
        out.append((pc, desc))
        pc += sz
    return regs, ins, out


cls = "Lbw0;"
print("Lbw0; method walk:")
for i in range(class_defs_size):
    off = class_defs_off + 32 * i
    cidx, = struct.unpack_from("<I", dex, off)
    if get_type(cidx) != cls:
        continue
    cfoff, = struct.unpack_from("<I", dex, off + 24)
    if cfoff == 0:
        continue
    pos = cfoff
    s, pos = uleb(dex, pos)
    ifc, pos = uleb(dex, pos)
    dm, pos = uleb(dex, pos)
    vm, pos = uleb(dex, pos)
    for _ in range(s):
        _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
    for _ in range(ifc):
        _, pos = uleb(dex, pos); _, pos = uleb(dex, pos)
    for kind in (dm, vm):
        midx = 0; code = 0
        for _ in range(kind):
            d, pos = uleb(dex, pos)
            fl, pos = uleb(dex, pos)
            cd, pos = uleb(dex, pos)
            midx += d
            _, mname = get_method(midx)
            if cd:
                code += cd
                if mname in ("a", "d", "k", "f"):
                    print(f"\n=== Lbw0;->{mname} code_off={code} ===")
                    disasm(code)
