#!/usr/bin/env python3
"""cont150_disasm2.py — accurate Dalvik disassembler for a named method.
Usage: cont150_disasm2.py <apk> <class-desc like Ltv0;> <method-name> [max]
Full instruction-size table (all 256 opcodes), string/type/field/method refs
resolved, branch targets printed. Designed for evidence-grade decodes."""
import struct, zipfile, sys

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
CLS = sys.argv[2] if len(sys.argv) > 2 else 'Lt4;'
METH = sys.argv[3] if len(sys.argv) > 3 else 'dispatchDraw'
MAXI = int(sys.argv[4]) if len(sys.argv) > 4 else 400

z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

hdr = {
    'str_size': 0x38, 'str_off': 0x3C, 'type_size': 0x40, 'type_off': 0x44,
    'proto_size': 0x48, 'proto_off': 0x4C, 'field_size': 0x50, 'field_off': 0x54,
    'meth_size': 0x58, 'meth_off': 0x5C, 'cls_size': 0x60, 'cls_off': 0x64,
}
str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
proto_off = struct.unpack_from('<I', dex, 0x4C)[0]
field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
fids = []
for i in range(field_size):
    ci, ti, ni = struct.unpack_from('<HHI', dex, field_off + i * 8)
    fids.append((tds[ci], tds[ti], str_at(ni)))
mids = []
for i in range(meth_size):
    ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + i * 8)
    pshort, _ = struct.unpack_from('<IH', dex, proto_off + pi * 12)[0:1], None
    proto_idx = struct.unpack_from('<I', dex, proto_off + pi * 12)[0]
    ret_idx = struct.unpack_from('<I', dex, proto_off + pi * 12 + 4)[0]
    mids.append((tds[ci], str_at(ni), tds[ret_idx] if ret_idx < type_size else '?'))

# ---- parse class_data_item: static fields, instance fields, direct + virtual methods
def parse_methods(off, cnt, is_direct, base=0):
    out = []
    p = off
    midx = base
    for _ in range(cnt):
        mdiff, p = uleb(dex, p)
        acc, p = uleb(dex, p)
        code_off, p = uleb(dex, p)
        midx += mdiff
        if code_off:
            out.append((midx, code_off, is_direct))
    return out, p

methods = []
target = None
for i in range(class_size):
    c = struct.unpack_from('<I', dex, class_off + i * 32)[0]
    if tds[c] == CLS:
        target = struct.unpack_from('<8I', dex, class_off + i * 32)
        break
if target is None:
    print(f'class {CLS} NOT FOUND'); sys.exit(1)
_, acc, sup, ifs, srcf, anno, cdata, svals = target
dm = vm = 0
if cdata:
    p = cdata
    sf_count, p = uleb(dex, p)
    if_count, p = uleb(dex, p)
    dm_count, p = uleb(dex, p)
    vm_count, p = uleb(dex, p)
    for _ in range(sf_count):
        _, p = uleb(dex, p); _, p = uleb(dex, p)
    for _ in range(if_count):
        _, p = uleb(dex, p); _, p = uleb(dex, p)
    dm = p
    methods, dm_end = parse_methods(dm, dm_count, True, base=0)
    # dex spec: direct_methods and virtual_methods are TWO separate encoded
    # method lists — each starts a FRESH method_idx_diff chain (verified:
    # Ltv0; dm1=13386 abs, vm1 diff=13388 = method_ids[13388]=Ltv0;.a).
    methods += parse_methods(dm_end, vm_count, False, base=0)[0]

found = None
for midx, code_off, is_dir in methods:
    ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + midx * 8)
    if tds[ci] == CLS and str_at(ni) == METH:
        found = (code_off, is_dir, mids[midx])
        break
if not found:
    print(f'method {CLS}.{METH} NOT FOUND (no code)'); sys.exit(1)
code_off, is_dir, mref = found
# code_item: registers(u16) ins(u16) outs(u16) tries(u16) debug_info_off(u32) insns_size(u32)
regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<4H2I', dex, code_off)
print(f'== {CLS}.{METH} {mref[2]} direct={is_dir} code@{code_off} regs={regs} ins={ins} outs={outs} insns={insns_size}')

# instruction size table: format sizes in 16-bit code units
# (opcode -> size). Standard dalvik table:
SIZES = [1]*256
for op in range(0x00, 0x12): SIZES[op] = 1
SIZES[0x12]=1; SIZES[0x13]=2; SIZES[0x14]=3; SIZES[0x15]=2; SIZES[0x16]=2
SIZES[0x17]=3; SIZES[0x18]=5; SIZES[0x19]=2
SIZES[0x1a]=2; SIZES[0x1b]=3; SIZES[0x1c]=2; SIZES[0x1d]=1; SIZES[0x1e]=1
SIZES[0x1f]=2; SIZES[0x20]=2; SIZES[0x21]=1; SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3; SIZES[0x27]=1
SIZES[0x28]=1; SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for op in range(0x2d, 0x31): SIZES[op]=2
SIZES[0x31]=2; SIZES[0x32]=2; SIZES[0x33]=2; SIZES[0x34]=2
for op in range(0x35, 0x3d): SIZES[op]=2
for op in range(0x3d, 0x45): SIZES[op]=2
SIZES[0x44]=2; SIZES[0x45]=2; SIZES[0x46]=2; SIZES[0x47]=2; SIZES[0x48]=2
SIZES[0x49]=2; SIZES[0x4a]=2; SIZES[0x4b]=2; SIZES[0x4c]=2; SIZES[0x4d]=2
SIZES[0x4e]=2; SIZES[0x4f]=2; SIZES[0x50]=2; SIZES[0x51]=2
for op in range(0x52, 0x5d): SIZES[op]=2
SIZES[0x5d]=2; SIZES[0x5e]=2; SIZES[0x5f]=2; SIZES[0x60]=2; SIZES[0x61]=2
SIZES[0x62]=2; SIZES[0x63]=2; SIZES[0x64]=2; SIZES[0x65]=2; SIZES[0x66]=2
SIZES[0x67]=2; SIZES[0x68]=2; SIZES[0x69]=2; SIZES[0x6a]=2
SIZES[0x6b]=2; SIZES[0x6c]=2; SIZES[0x6d]=2; SIZES[0x6e]=3; SIZES[0x6f]=3
SIZES[0x70]=3; SIZES[0x71]=3; SIZES[0x72]=3
for op in range(0x73, 0x74): SIZES[op]=1
SIZES[0x74]=3; SIZES[0x75]=3; SIZES[0x76]=3; SIZES[0x77]=3; SIZES[0x78]=3
for op in range(0x79, 0x7a): SIZES[op]=1
for op in range(0x7b, 0x90): SIZES[op]=1
for op in range(0x90, 0xb1): SIZES[op]=2
for op in range(0xb1, 0xd0): SIZES[op]=2
SIZES[0xd0]=2; SIZES[0xd1]=2
for op in range(0xd2, 0xe3): SIZES[op]=2
for op in range(0xe3, 0x100): SIZES[op]=1  # unused/ODEX

NAMES = {0x00:'nop',0x01:'move',0x02:'move/from16',0x03:'move/16',0x04:'move-wide',0x05:'move-wide/from16',0x06:'move-wide/16',0x07:'move-object',0x08:'move-object/from16',0x09:'move-object/16',0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch',0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short',0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short',0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',0x7b:'int-to-long',0x7c:'int-to-float',0x7d:'int-to-double',0x7e:'long-to-int',0x7f:'long-to-float',0x80:'long-to-double',0x81:'float-to-int',0x82:'float-to-long',0x83:'float-to-double',0x84:'double-to-int',0x85:'double-to-long',0x86:'double-to-float',0x87:'int-to-byte',0x88:'int-to-char',0x89:'int-to-short',0x8a:'add-int',0x8b:'sub-int',0x8c:'mul-int',0x8d:'div-int',0x8e:'rem-int',0x8f:'and-int',0x90:'or-int',0x91:'xor-int',0x92:'shl-int',0x93:'shr-int',0x94:'ushr-int',0x95:'add-long',0x96:'sub-long',0x97:'mul-long',0x98:'div-long',0x99:'rem-long',0x9a:'and-long',0x9b:'or-long',0x9c:'xor-long',0x9d:'shl-long',0x9e:'shr-long',0x9f:'ushr-long',0xa0:'add-float',0xa1:'sub-float',0xa2:'mul-float',0xa3:'div-float',0xa4:'rem-float',0xa5:'add-double',0xa6:'sub-double',0xa7:'mul-double',0xa8:'div-double',0xa9:'rem-double',0xaa:'add-int/2addr',0xab:'sub-int/2addr',0xac:'mul-int/2addr',0xad:'div-int/2addr',0xae:'rem-int/2addr',0xaf:'and-int/2addr',0xb0:'or-int/2addr',0xb1:'xor-int/2addr',0xb2:'shl-int/2addr',0xb3:'shr-int/2addr',0xb4:'ushr-int/2addr',0xb5:'add-long/2addr',0xb6:'sub-long/2addr',0xb7:'mul-long/2addr',0xb8:'div-long/2addr',0xb9:'rem-long/2addr',0xba:'and-long/2addr',0xbb:'or-long/2addr',0xbc:'xor-long/2addr',0xbd:'shl-long/2addr',0xbe:'shr-long/2addr',0xbf:'ushr-long/2addr',0xc0:'add-float/2addr',0xc1:'sub-float/2addr',0xc2:'mul-float/2addr',0xc3:'div-float/2addr',0xc4:'rem-float/2addr',0xc5:'add-double/2addr',0xc6:'sub-double/2addr',0xc7:'mul-double/2addr',0xc8:'div-double/2addr',0xc9:'rem-double/2addr',0xca:'add-int/lit16',0xcb:'rsub-int',0xcc:'mul-int/lit16',0xcd:'div-int/lit16',0xce:'rem-int/lit16',0xcf:'and-int/lit16',0xd0:'or-int/lit16',0xd1:'xor-int/lit16',0xd2:'add-int/lit8',0xd3:'rsub-int/lit8',0xd4:'mul-int/lit8',0xd5:'div-int/lit8',0xd6:'rem-int/lit8',0xd7:'and-int/lit8',0xd8:'or-int/lit8',0xd9:'xor-int/lit8',0xda:'shl-int/lit8',0xdb:'shr-int/lit8',0xdc:'ushr-int/lit8'}

code = dex[code_off + 16 : code_off + 16 + insns_size * 2]
pc = 0
while pc < insns_size and pc < MAXI:
    op = code[pc * 2]
    sz = SIZES[op]
    raw = code[pc*2 : min(pc*2+sz*2, len(code))]
    if len(raw) < 4:  # clamp-safe padding for 4-byte readers (branches, consts)
        raw = raw + b'\x00' * (4 - len(raw))
    name = NAMES.get(op, f'op0x{op:02x}')
    detail = ''
    if op in (0x1a,):  # const-string
        bidx = struct.unpack_from('<H', raw, 2)[0]
        detail = f'"{str_at(bidx)}"'
    elif op == 0x1b:
        bidx = struct.unpack_from('<I', raw, 2)[0]
        detail = f'"{str_at(bidx)}"'
    elif op in (0x1c, 0x1f, 0x20, 0x22, 0x23, 0x24, 0x25, 0x27):
        tidx = struct.unpack_from('<H', raw, 2)[0]
        if tidx < type_size: detail = tds[tidx]
    elif 0x52 <= op <= 0x6d:
        fidx = struct.unpack_from('<H', raw, 2)[0]
        if fidx < field_size:
            fc, ft, fn = fids[fidx]
            detail = f'{fc}.{fn}:{ft}'
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        midx2 = struct.unpack_from('<H', raw, 2)[0]
        if midx2 < meth_size:
            mc, mn, mr = mids[midx2]
            detail = f'{mc}.{mn} -> {mr}'
    elif op in (0x74, 0x75, 0x76, 0x77, 0x78):
        midx2 = struct.unpack_from('<H', raw, 2)[0]
        if midx2 < meth_size:
            mc, mn, mr = mids[midx2]
            detail = f'{mc}.{mn} -> {mr}'
    elif op == 0x28:
        off2 = struct.unpack_from('<b', raw, 1)[0]
        detail = f'-> {pc + off2}'
    elif op == 0x29:
        off2 = struct.unpack_from('<h', raw, 2)[0]
        detail = f'-> {pc + off2}'
    elif op == 0x2a:
        off2 = struct.unpack_from('<i', raw, 2)[0]
        detail = f'-> {pc + off2}'
    elif 0x32 <= op <= 0x37:
        off2 = struct.unpack_from('<h', raw, 2)[0]  # format 22t: target in 2nd u16
        detail = f'-> {pc + off2}'
    elif 0x38 <= op <= 0x3d:
        off2 = struct.unpack_from('<h', raw, 2)[0]
        detail = f'-> {pc + off2}'
    elif op in (0x2b, 0x2c):
        poff = pc + struct.unpack_from('<i', raw, 2)[0]
        detail = f'table@{poff}'
    elif op == 0x12:
        lit = struct.unpack_from('<b', raw, 1)[0] & 0xF
        litb = (struct.unpack_from('<B', raw, 1)[0] >> 4) & 0xF
        detail = f'v{(litb)}={lit if lit < 8 else lit - 16}'
    elif op == 0x13:
        vb, lit = struct.unpack_from('<BH', raw, 0)[0:2]
        detail = f'v{raw[1]&0xf}={struct.unpack_from("<h", raw, 2)[0]}'
    elif op == 0x14:
        detail = f'v{raw[1]&0xf}={struct.unpack_from("<i", raw, 2)[0]}'
    elif op == 0x15:
        detail = f'v{raw[1]&0xf}=0x{struct.unpack_from("<H", raw, 2)[0]:04x}0000'
    elif op in (0x0f, 0x10, 0x11):
        detail = f'v{raw[1]&0xf}'
    elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
        detail += f' v{raw[1]&0xf}, v{(raw[1]>>4)&0xf}'
    elif op in (0x6e,0x6f,0x70,0x71,0x72):
        b21 = struct.unpack_from('<H', raw, 4)[0]
        cnt = (b21 >> 12) & 0xF
        gs = (b21 & 0xFFF)
        regs_l = []
        if cnt == 1: regs_l=[gs&0xf]
        elif cnt == 2: regs_l=[gs&0xf,(gs>>4)&0xf]
        elif cnt == 3: regs_l=[gs&0xf,(gs>>4)&0xf,(gs>>8)&0xf]
        elif cnt == 4: regs_l=[gs&0xf,(gs>>4)&0xf,(gs>>8)&0xf,(gs>>12)&0xf]
        elif cnt == 5: regs_l=[gs&0xf,(gs>>4)&0xf,(gs>>8)&0xf,(gs>>12)&0xf,b21>>12]
        detail += ' ' + ','.join(f'v{r}' for r in regs_l)
    print(f'  {pc:04d}: {name} {detail}')
    pc += sz
