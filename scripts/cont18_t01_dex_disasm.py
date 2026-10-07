#!/usr/bin/env python3
"""CONT-18 T-01: disassemble the extracted kotlinx MutexImpl.unlock /
SemaphoreAndMutexImpl.release bytecode from the corpus DEX — the source-first
reconstruction of the F-217 waiter-resume algorithm."""
import struct, sys, zipfile, io, json

ARG = sys.argv[1] if len(sys.argv) > 1 else 'tmp/f217_dex/classes.dex'
if ARG.endswith('.apk'):
    z = zipfile.ZipFile(ARG)
    dex_names = [n for n in z.namelist() if n.endswith('.dex')]
else:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as t:
        t.write(ARG, 'classes.dex')
    z = zipfile.ZipFile(buf)
    dex_names = ['classes.dex']

OPC = {
 0x00:'nop',0x01:'move',0x04:'move-wide',0x07:'move-object',0x0a:'move-result',
 0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
 0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
 0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',
 0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',
 0x1a:'const-string',0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',
 0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',
 0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',
 0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',
 0x2b:'packed-switch',0x2c:'sparse-switch',
 0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',0x30:'cmpg-double',
 0x31:'cmp-long',
 0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
 0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',
 0x3d:'if-lez',
 0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',
 0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',
 0x4f:'aput-byte',0x52:'iget',0x53:'iget-wide',0x54:'iget-object',
 0x55:'iget-boolean',0x56:'iget-byte',0x59:'iput',0x5a:'iput-wide',
 0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',
 0x5e:'sget',0x5f:'sget-wide',0x60:'sget-object',0x61:'sget-boolean',
 0x62:'sget-byte',
 0x63:'sput',0x64:'sput-wide',0x65:'sput-object',0x66:'sput-boolean',
 0x67:'sput-byte',
 0x68:'sget-volatile',0x6d:'sput-volatile',0x70:'invoke-virtual',
 0x71:'invoke-super',0x72:'invoke-direct',0x73:'invoke-static',
 0x74:'invoke-virtual/range',0x76:'invoke-direct/range',
 0x77:'invoke-static/range',
 0x78:'invoke-interface',0x79:'invoke-interface/range',
 0x7b:'neg-int',0x7c:'not-int',0x7d:'neg-long',
 0x7f:'int-to-long',0x80:'int-to-float',0x81:'int-to-double',
 0x82:'long-to-int',0x83:'long-to-float',0x84:'long-to-double',
 0x85:'float-to-int',0x86:'float-to-long',0x87:'float-to-double',
 0x88:'double-to-int',0x89:'double-to-long',0x8a:'double-to-float',
 0x8b:'int-to-byte',0x8c:'int-to-char',0x8d:'int-to-short',
 0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',
 0x95:'and-int',0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',
 0x9a:'ushr-int',
 0x9b:'add-long',0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',
 0x9f:'and-long',0xa0:'or-long',0xa1:'xor-long',0xa2:'shl-long',0xa3:'shr-long',
 0xa4:'ushr-long',
 0xa5:'add-float',0xa6:'sub-float',0xa7:'mul-float',0xa8:'div-float',
 0xab:'add-double',0xac:'sub-double',0xad:'mul-double',0xae:'div-double',
 0xaf:'add-int/2addr',0xb0:'sub-int/2addr',0xb1:'mul-int/2addr',
 0xb2:'div-int/2addr',0xb3:'rem-int/2addr',0xb4:'and-int/2addr',
 0xb5:'or-int/2addr',0xb6:'xor-int/2addr',0xb7:'shl-int/2addr',
 0xb8:'shr-int/2addr',0xb9:'ushr-int/2addr',
 0xba:'add-long/2addr',0xbb:'sub-long/2addr',0xbc:'mul-long/2addr',
 0xbd:'div-long/2addr',0xbe:'and-long/2addr',0xbf:'or-long/2addr',
 0xc0:'xor-long/2addr',0xc1:'shl-long/2addr',0xc2:'shr-long/2addr',
 0xc3:'ushr-long/2addr',
 0xc4:'add-float/2addr',0xc5:'sub-float/2addr',0xc6:'mul-float/2addr',
 0xc7:'div-float/2addr',
 0xc8:'add-double/2addr',0xc9:'sub-double/2addr',0xca:'mul-double/2addr',
 0xcb:'div-double/2addr',
 0xd0:'add-int/lit16',0xd1:'rsub-int',0xd2:'mul-int/lit16',0xd3:'div-int/lit16',
 0xd4:'rem-int/lit16',0xd5:'and-int/lit16',0xd6:'or-int/lit16',
 0xd7:'xor-int/lit16',0xd8:'add-int/lit8',0xd9:'rsub-int/lit8',
 0xda:'mul-int/lit8',0xdb:'div-int/lit8',0xdc:'rem-int/lit8',
 0xdd:'and-int/lit8',0xde:'or-int/lit8',0xdf:'xor-int/lit8',
 0xe0:'shl-int/lit8',0xe1:'shr-int/lit8',0xe2:'ushr-int/lit8',
}

SIZES_22B = {0x20,0x21,0x22,0x23,0x1c,0x1f,0x12,0x13,0x15,0x16,0x19,0x1a,
             0x54,0x55,0x56,0x52,0x53,0x5b,0x5c,0x5d,0x59,0x5a,0x60,0x61,0x62,
             0x5e,0x65,0x66,0x67,0x63,0x64,0x68,0x6d,0x70,0x71,0x72,0x73,
             0x78,0x7b,0x7c,0x7d,0x7f,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,
             0x88,0x89,0x8a,0x8b,0x8c,0x8d,0xa5,0xa6,0xa7,0xa8,0xab,0xac,0xad,
             0xae,0x0f,0x10,0x11,0x0a,0x0b,0x0c,0x01,0x04,0x07,0x3c,0x3d,0x38,
             0x39,0x3a,0x3b,0x2b,0x2c,0x26,0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,
             0xd7,0xd8,0xd9,0xda,0xdb,0xdc,0xdd,0xde,0xdf,0xe0,0xe1,0xe2}

def disasm(b, string_off, type_off, field_off, method_off, get_string, get_type):
    n = len(b) // 2
    out = []
    i = 0
    while i < n:
        pc = i * 2
        op = b[i * 2]
        if op in (0x00,0x0e,0x0d):
            out.append(f"{pc:04x}: {OPC.get(op,'?')}")
            i += 1; continue
        if op in (0x01,0x04,0x07,0x0a,0x0b,0x0c,0x0f,0x10,0x11,0x1d,0x1e,
                  0x27,0x28,0x7b,0x7c,0x7d,0x21):
            if op == 0x28:
                out.append(f"{pc:04x}: goto +{b[i*2+1]}")
            elif op == 0x00:
                out.append(f"{pc:04x}: nop")
            else:
                va = (b[i*2+1] >> 4) & 0xf
                vb2 = b[i*2+1] & 0xf if i*2+1 < len(b) else 0
                out.append(f"{pc:04x}: {OPC.get(op,'?')} v{va}" +
                           (f", v{vb2}" if op in (0x01,0x04,0x07) else ""))
            i += 1; continue
        # default: 2-unit (22b/22/21c shapes) — print raw operands + ref when known
        raw = b[i*2:i*2+4]
        hi = b[i*2+1]
        if op in (0x1a,):
            sidx = struct.unpack_from('<H', raw, 2)[0]
            out.append(f"{pc:04x}: const-string v{b[i*2+2]>>4}, \"{get_string(sidx)[:48]}\"")
        elif op in (0x1c,0x1f,0x22,0x24,0x25,0x20,0x23):
            tidx = struct.unpack_from('<H', raw, 2)[0]
            out.append(f"{pc:04x}: {OPC.get(op,'?')} type={get_type(tidx)}")
        elif op in (0x52,0x53,0x54,0x55,0x56,0x59,0x5a,0x5b,0x5c,0x5d,
                    0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x6d):
            fidx = struct.unpack_from('<H', raw, 2)[0]
            cls, typ, nam = field_ref(fidx)
            out.append(f"{pc:04x}: {OPC.get(op,'?')} v?, {cls}.{nam}")
        elif op in (0x70,0x71,0x72,0x73,0x78):
            midx = struct.unpack_from('<H', raw, 2)[0]
            cls, mnam = method_ref(midx)
            out.append(f"{pc:04x}: {OPC.get(op,'?')} {cls}.{mnam}")
        elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
            t = struct.unpack_from('<h', raw, 2)[0]
            out.append(f"{pc:04x}: {OPC.get(op,'?')} -> {pc + t*2:04x}")
        elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
            t = struct.unpack_from('<h', raw, 2)[0]
            out.append(f"{pc:04x}: {OPC.get(op,'?')} v{b[i*2+1]} -> {pc + t*2:04x}")
        else:
            out.append(f"{pc:04x}: {OPC.get(op,hex(op))} {raw.hex()}")
        i += 2
        # instructions can be 1,2,3 units; approximate by 2-unit default and
        # 3-unit for known 35c/45cc shapes
    return out

for dn in dex_names:
    b = z.read(dn)
    string_ids_size, string_ids_off = struct.unpack_from('<II', b, 0x38)
    type_ids_size, type_ids_off = struct.unpack_from('<II', b, 0x40)
    proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 0x48)
    field_ids_size, field_ids_off = struct.unpack_from('<II', b, 0x50)
    method_ids_size, method_ids_off = struct.unpack_from('<II', b, 0x58)
    class_defs_size, class_defs_off = struct.unpack_from('<II', b, 0x60)

    def get_string(idx):
        off = struct.unpack_from('<I', b, string_ids_off + 4 * idx)[0]
        r = 0; s = 0
        while True:
            by = b[off]; off += 1
            r |= (by & 0x7f) << s
            if not (by & 0x80): break
            s += 7
        end = b.index(b'\x00', off)
        return b[off:end].decode('utf-8', 'replace')

    def get_type(idx):
        si = struct.unpack_from('<I', b, type_ids_off + 4 * idx)[0]
        return get_string(si)

    def field_ref(idx):
        cls, typ, nam = struct.unpack_from('<HHI', b, field_ids_off + 8 * idx)
        return get_type(cls), get_type(typ), get_string(nam)

    def method_ref(idx):
        cls, proto, nam = struct.unpack_from('<HHI', b, method_ids_off + 8 * idx)
        return get_type(cls), get_string(nam)

    for ci in range(class_defs_size):
        off = class_defs_off + 32 * ci
        cls = get_type(struct.unpack_from('<I', b, off)[0])
        if cls not in ('Lkotlinx/coroutines/sync/MutexImpl;',
                       'Lkotlinx/coroutines/sync/SemaphoreAndMutexImpl;'):
            continue
        class_data_off = struct.unpack_from('<I', b, off + 24)[0]
        p = class_data_off
        def uleb(buf, o):
            r = 0; s = 0
            while True:
                by = buf[o]; o += 1
                r |= (by & 0x7f) << s
                if not (by & 0x80): break
                s += 7
            return r, o
        sf_n, o1 = uleb(b, p); if_n, o2 = uleb(b, o1)
        dm_n, o3 = uleb(b, o2); vm_n, o4 = uleb(b, o3)
        p = o4
        for _ in range(sf_n + if_n):
            _, p = uleb(b, p); _, p = uleb(b, p)
        want = ('unlock', 'release', 'tryLockImpl', 'lock$suspendImpl')
        for kind, count in (('direct', dm_n), ('virtual', vm_n)):
            midx = 0
            for _ in range(count):
                d, p = uleb(b, p); midx += d
                acc, p = uleb(b, p)
                code_off, p = uleb(b, p)
                if code_off == 0: continue
                _mi_cls, _mi_proto, _mi_nam_idx = struct.unpack_from(
                    '<HHI', b, method_ids_off + 8 * midx)
                mnam = get_string(_mi_nam_idx)
                if mnam not in want: continue
                regs, ins, outs, tries, dbg, insns_sz = struct.unpack_from(
                    '<HHHHII', b, code_off)
                insns = b[code_off + 16: code_off + 16 + insns_sz * 2]
                print(f"=== {cls}->{mnam}  insns={insns_sz} regs={regs} ins={ins} outs={outs}")
                for line in disasm(insns, string_ids_off, type_ids_off,
                                   field_ids_off, method_ids_off,
                                   get_string, get_type):
                    print("   ", line)
