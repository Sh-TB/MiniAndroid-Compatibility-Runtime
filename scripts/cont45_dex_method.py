#!/usr/bin/env python3
"""CONT-45 D1: dump method descriptor + bytecode from dooz APK (multi-dex).
Usage: cont45_dex_method.py <class-Ldesc> <method>"""
import sys, zipfile, struct

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGET_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lel0;'
TARGET_METHOD = sys.argv[2] if len(sys.argv) > 2 else 'q'

z = zipfile.ZipFile(APK)
ALL_DEXES = [(n, z.read(n)) for n in z.namelist() if n.endswith('.dex')]
print(f"loaded {len(ALL_DEXES)} dex files")

OPS = {0x00:'nop',0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
       0x12:'const/4',0x13:'const/16',0x1a:'const-string',0x1c:'const-class',
       0x1f:'check-cast',0x21:'array-length',0x22:'new-instance',0x23:'new-array',
       0x28:'goto',0x29:'goto/16',0x2b:'goto/32',0x2c:'packed-switch',0x2d:'sparse-switch',
       0x31:'if-eq',0x32:'if-ne',0x33:'if-lt',0x34:'if-ge',0x35:'if-gt',0x36:'if-le',
       0x37:'if-eqz',0x38:'if-nez',0x39:'if-ltz',0x3a:'if-gez',0x3b:'if-gtz',0x3c:'if-lez',
       0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',
       0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
       0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-short',0x5f:'iput-char',
       0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
       0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x6a:'sput',0x6b:'sput-wide',
       0x6c:'sput-object',0x6d:'sput-boolean',
       0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
       0x71:'invoke-static',0x72:'invoke-interface',
       0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
       0x77:'invoke-static/range',0x78:'invoke-interface/range'}
WIDE = {0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78,0x2b,0x2c,0x2d}
ONE = set(range(0x52,0x67)) | {0x1a,0x1c,0x1f,0x21,0x22,0x23,0x13,0x15,0x16,0x17,0x19,0x29,0x31,0x32,0x33,0x34,0x35,0x36,0x02,0x05,0x08,0x0c,0x0d,0x20,0x24,0x25}

def decode(d, field_ids_off, method_ids_off, code_off):
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', d, code_off)
    print(f"  regs={regs} ins={ins} outs={outs} insns={insns_size}")
    code = d[code_off+16: code_off+16+insns_size*2]
    pc = 0
    while pc < insns_size:
        w = struct.unpack_from('<H', code, pc*2)[0]
        op = w & 0xff; aa = (w>>8)&0xff
        nm = OPS.get(op, f'op_{op:02x}')
        extra = ''
        if op in (0x54,0x55,0x56,0x57,0x58,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x6a,0x6b,0x6c,0x6d):
            bx = struct.unpack_from('<H', code, (pc+1)*2)[0]
            fcls, ftype, fname = struct.unpack_from('<HHI', d, field_ids_off + bx*8)
            extra = f' {get_string(fcls_idx)}...' if False else ''
        pc += 1

for dexname, d in ALL_DEXES:
    string_ids_size, string_ids_off = struct.unpack_from('<II', d, 56)
    type_ids_size, type_ids_off = struct.unpack_from('<II', d, 64)
    proto_ids_size, proto_ids_off = struct.unpack_from('<II', d, 72)
    field_ids_size, field_ids_off = struct.unpack_from('<II', d, 80)
    method_ids_size, method_ids_off = struct.unpack_from('<II', d, 88)
    class_defs_size, class_defs_off = struct.unpack_from('<II', d, 96)

    def get_string(idx):
        off = struct.unpack_from('<I', d, string_ids_off + idx*4)[0]
        n = 0; shift = 0; p = off
        while True:
            b = d[p]; p += 1
            n |= (b & 0x7f) << shift
            if not (b & 0x80): break
            shift += 7
        end = d.find(b'\x00', p)
        return d[p:end].decode('utf-8', 'replace')

    def get_type(idx):
        si = struct.unpack_from('<I', d, type_ids_off + idx*4)[0]
        return get_string(si)

    def get_method(idx):
        cls_idx, proto_idx, name_idx = struct.unpack_from('<HHI', d, method_ids_off + idx*8)
        if proto_idx > proto_ids_size:
            print(f"DBG idx={idx} cls_idx={cls_idx} proto_idx={proto_idx} name_idx={name_idx} method_ids_off={method_ids_off}")
            sys.exit(1)
        shorty_idx, return_idx, params_off = struct.unpack_from('<III', d, proto_ids_off + proto_idx*12)
        params = []
        if params_off:
            n = struct.unpack_from('<I', d, params_off)[0]
            for i in range(n):
                ti = struct.unpack_from('<H', d, params_off + 4 + i*2)[0]
                params.append(get_type(ti))
        return get_type(cls_idx), get_string(name_idx), params, get_type(return_idx)

    def uleb128(p):
        n = 0; shift = 0
        while True:
            b = d[p]; p += 1
            n |= (b & 0x7f) << shift
            if not (b & 0x80): break
            shift += 7
        return n, p

    for i in range(class_defs_size):
        off = class_defs_off + i*32
        cls_idx, access, super_idx, interfaces_off, source_idx, anno_off, cd_off, static_v, instance_v = struct.unpack_from('<IIIIIIIII', d, off)
        if get_type(cls_idx) != TARGET_CLASS:
            continue
        p = cd_off
        sf, p = uleb128(p); inf, p = uleb128(p); dm, p = uleb128(p); vm, p = uleb128(p)
        def skip_fields(n, p):
            for _ in range(n):
                _, p = uleb128(p); _, p = uleb128(p)
            return p
        p = skip_fields(sf, p); p = skip_fields(inf, p)
        for kind, count in (('DIRECT', dm), ('VIRTUAL', vm)):
            mi = 0
            for _ in range(count):
                delta, p = uleb128(p); mi += delta
                acc, p = uleb128(p); code_off, p = uleb128(p)
                if mi >= method_ids_size:
                    print(f"BAD midx {mi} at {kind} (max {method_ids_size}) -- stopping")
                    sys.exit(1)
                mcls, name, params, ret = get_method(mi)
                if name == TARGET_METHOD:
                    print(f"{kind} {mcls}.{name}{params}{ret} acc=0x{acc:x} code_off=0x{code_off:x} dex={dexname}")
                    if code_off:
                        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', d, code_off)
                        print(f"  regs={regs} ins={ins} outs={outs} insns={insns_size}")
                        code = d[code_off+16: code_off+16+insns_size*2]
                        pc = 0
                        while pc < insns_size:
                            w = struct.unpack_from('<H', code, pc*2)[0]
                            op = w & 0xff; aa = (w>>8)&0xff
                            nm = OPS.get(op, f'op_{op:02x}')
                            extra = ''
                            if op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x6a,0x6b,0x6c,0x6d):
                                bx = struct.unpack_from('<H', code, (pc+1)*2)[0]
                                fcls, ftype, fname = struct.unpack_from('<HHI', d, field_ids_off + bx*8)
                                extra = f' {get_type(fcls)}.{get_string(fname)}:{get_type(ftype)}'
                            elif op in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78):
                                bx = struct.unpack_from('<H', code, (pc+1)*2)[0]
                                mcls2, mname2, mparams, mret = get_method(bx)
                                extra = f' {mcls2}.{mname2}{mparams}{mret}'
                            elif op == 0x1a:
                                bx = struct.unpack_from('<H', code, (pc+1)*2)[0]
                                extra = f' "{get_string(bx)}"'
                            elif op in (0x37,0x38,0x39,0x3a,0x3b,0x3c):
                                ab = struct.unpack_from('<b', code, (pc+1)*2)[0]
                                extra = f' -> +{ab} (v{aa})'
                            elif op in (0x31,0x32,0x33,0x34,0x35,0x36):
                                ab = struct.unpack_from('<b', code, (pc+1)*2)[0]
                                extra = f' -> +{ab}'
                            elif op == 0x12:
                                extra = f' v{aa&0xf}, {(aa>>4)&0xf}'
                            elif op == 0x22:
                                bx = struct.unpack_from('<H', code, (pc+1)*2)[0]
                                extra = f' {get_type(bx)}'
                            print(f'  {pc:04d}: {nm}{extra}')
                            pc += 3 if op in WIDE else 2 if op in ONE else 1
        sys.exit(0)
print("METHOD NOT FOUND")
