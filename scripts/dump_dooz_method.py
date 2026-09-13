#!/usr/bin/env python3
"""Dump raw bytecode of a method from dooz APK (EXP-051 tool, dooz paths).
Usage: dump_dooz_method.py <class-Ldesc> <method> [descriptor-prefix]
"""
import sys, zipfile, struct

apk = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'
target_class = sys.argv[1] if len(sys.argv) > 1 else 'Landroidx/compose/ui/node/e;'
target_method = sys.argv[2] if len(sys.argv) > 2 else 'G'
desc_prefix = sys.argv[3] if len(sys.argv) > 3 else ''

OPS_1 = {0x00:'nop',0x0e:'return-void',0x1d:'monitor-enter',0x1e:'monitor-exit',
         0x26:'throw',0x27:'goto'}
OPS_2_12x = {0x01:'move',0x04:'move-wide',0x07:'move-object',
             0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',
             0x0d:'move-exception',0x0f:'return',0x10:'return-wide',0x11:'return-object',
             0x12:'const/4',0x21:'array-length'}
OPS_2_22x = {0x02:'move/from16',0x05:'move-wide/from16',0x08:'move-object/from16'}
OPS_3_32x = {0x03:'move/16',0x06:'move-wide/16',0x09:'move-object/16'}
OPS_2_21 = {0x13:'const/16',0x15:'const/high16',0x16:'const-wide/16',
            0x17:'const-wide/32',0x19:'const-wide/high16',0x1c:'const-class',
            0x1f:'check-cast',0x22:'new-instance',0x28:'goto/16',
            0x37:'if-eqz',0x38:'if-nez',0x39:'if-ltz',0x3a:'if-gez',
            0x3b:'if-gtz',0x3c:'if-lez'}
OPS_2_22 = {0x20:'instance-of',0x23:'new-array',0x31:'if-eq',0x32:'if-ne',
            0x33:'if-lt',0x34:'if-ge',0x35:'if-gt',0x36:'if-le'}
OPS_2_22c = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
             0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',
             0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',
             0x5d:'iput-byte',0x5e:'iput-short',0x5f:'iput-char',
             0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
             0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',
             0x6a:'sput',0x6b:'sput-wide',0x6c:'sput-object',0x6d:'sput-boolean',
             0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
             0x71:'invoke-static',0x72:'invoke-interface'}
OPS_3_35c = {0x6e:'invoke-virtual/range',0x6f:'invoke-super/range',
             0x70:'invoke-direct/range',0x71:'invoke-static/range',
             0x72:'invoke-interface/range',0x74:'invoke-virtual/range',
             0x75:'invoke-super/range',0x76:'invoke-direct/range',
             0x77:'invoke-static/range',0x78:'invoke-interface/range'}
OPS_2_22s = {0x12:'const/4'}

def uleb128(f):
    result = 0; shift = 0
    while True:
        b = f.read(1)[0]
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80): break
    return result

with zipfile.ZipFile(apk) as z:
    dex_names = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
    for dex_name in dex_names:
        data = z.read(dex_name)
        # header
        string_ids_size, string_ids_off = struct.unpack_from('<II', data, 0x38)
        type_ids_size, type_ids_off = struct.unpack_from('<II', data, 0x40)
        proto_ids_size, proto_ids_off = struct.unpack_from('<II', data, 0x48)
        field_ids_size, field_ids_off = struct.unpack_from('<II', data, 0x50)
        method_ids_size, method_ids_off = struct.unpack_from('<II', data, 0x58)
        class_defs_size, class_defs_off = struct.unpack_from('<II', data, 0x60)

        def get_string(idx):
            off = struct.unpack_from('<I', data, string_ids_off + idx*4)[0]
            f = __import__('io').BytesIO(data)
            f.seek(off)
            n = uleb128(f)
            raw = f.read(n*1)
            # MUTF-8: skip quick scan, decode roughly
            s = raw.decode('utf-8', errors='replace')
            if s.endswith('\x00'): s = s[:-1]
            return s

        def get_type_desc(idx):
            si = struct.unpack_from('<I', data, type_ids_off + idx*4)[0]
            return get_string(si)

        # find class
        for ci in range(class_defs_size):
            off = class_defs_off + ci*32
            class_idx, access, superclass, interfaces, source, anno, cdata, static_vals = struct.unpack_from('<8I', data, off)
            if get_type_desc(class_idx) != target_class:
                continue
            # class_data_off is the 7th field
            cdo = struct.unpack_from('<I', data, off+24)[0]
            if cdo == 0:
                print(f"{target_class} has no class_data"); sys.exit(0)
            f = __import__('io').BytesIO(data); f.seek(cdo)
            sf = uleb128(f); inf = uleb128(f); dm = uleb128(f); vm = uleb128(f)
            # static fields
            for _ in range(sf): uleb128(f); uleb128(f)
            for _ in range(inf): uleb128(f); uleb128(f)
            for _ in range(dm):
                midx = uleb128(f); acc = uleb128(f); code_off = uleb128(f)
                if code_off == 0: continue
                mi = struct.unpack_from('<I', data, method_ids_off + midx*4)[0] if False else midx
                # method_id: class_idx(u16) proto_idx(u16) name_idx(u32)
                m_class, m_proto, m_name = struct.unpack_from('<HHI', data, method_ids_off + midx*8)
                name = get_string(m_name)
                if name != target_method: continue
                # proto: shorty_idx, return_idx, params_off
                poff = proto_ids_off + m_proto*12
                ret_idx = struct.unpack_from('<I', data, poff+4)[0]
                params_off = struct.unpack_from('<I', data, poff+8)[0]
                desc = get_type_desc(ret_idx)
                plist = []
                if params_off:
                    psz = struct.unpack_from('<I', data, params_off)[0]
                    for pi in range(psz):
                        plist.append(get_type_desc(struct.unpack_from('<H', data, params_off+4+pi*2)[0]))
                full = '(' + ''.join(plist) + ')' + desc
                if desc_prefix and not full.startswith(desc_prefix): continue
                print(f"=== {target_class}.{name}{full} code_off=0x{code_off:x} (dex {dex_name})")
                registers_size, ins_size, outs_size, tries_size, debug_info_off, insns_size = struct.unpack_from('<HHHHII', data, code_off)
                print(f"registers={registers_size} ins={ins_size} outs={outs_size} insns={insns_size}")
                insns = data[code_off+16 : code_off+16+insns_size*2]
                # disassemble 16-bit units
                i = 0
                units = struct.unpack_from(f'<{insns_size}H', insns, 0) if insns_size else ()
                while i < insns_size:
                    u = units[i]
                    op = u & 0xff
                    name = OPS_1.get(op) or OPS_2_12x.get(op) or OPS_2_22x.get(op) or OPS_3_32x.get(op) or OPS_2_21.get(op) or OPS_2_22.get(op) or OPS_2_22c.get(op) or OPS_2_22s.get(op) or OPS_3_35c.get(op)
                    size = 1
                    # instruction sizes by format (approximate standard widths)
                    fmt2 = set(OPS_2_12x)|set(OPS_2_21)|set(OPS_2_22)|set(OPS_2_22c)|set(OPS_2_22s)|{0x0d,0x0c,0x0a,0x0b,0x0f,0x10,0x11,0x1d,0x1e,0x21,0x27}
                    fmt3 = set(OPS_2_22x)|{0x22}
                    if op in OPS_1: size = 1
                    elif op in fmt2: size = 2
                    elif op in fmt3: size = 3
                    elif op in OPS_3_32x: size = 4
                    elif op in {0x6e,0x6f,0x70,0x71,0x72}: size = 3
                    elif op in {0x74,0x75,0x76,0x77,0x78}: size = 4
                    elif op == 0x00 and (u >> 8) == 0x01:  # nop/packed-switch
                        ident = (u >> 8) & 0xff
                        if ident == 0x01:
                            width = struct.unpack_from('<I', insns, (i+1)*2)[0]
                            size = (width*2) + 4
                            print(f"  {i:04d}: packed-switch-payload width={width}")
                            i += size; continue
                        elif ident == 0x02:
                            width = struct.unpack_from('<H', insns, (i+1)*2)[0]
                            size = (width*4) + 2
                            print(f"  {i:04d}: sparse-switch-payload width={width}")
                            i += size; continue
                        else:
                            size = 2
                    elif op == 0x1a or op == 0x1b: size = 2 if op==0x1a else 3  # const-string
                    elif op == 0x18: size = 5  # const-wide/high16? actually 2
                    elif op in {0x14,0x15,0x16,0x17}: size = 2
                    elif op in {0x23}: size = 2
                    elif op == 0x25: size = 3  # filled-new-array
                    elif op == 0x24: size = 3
                    elif op == 0x29: size = 3  # goto/32? no, 0x29=goto/32? actually goto/32=0x2a
                    elif op in {0x2a,0x2b,0x2c}: size = 3
                    elif op == 0x26: size = 3  # throw wide? throw=0x27; 0x26=goto/32
                    else:
                        # fallback: guess 2
                        size = 2
                    if name is None: name = f'op_{op:02x}'
                    detail = ''
                    if name.startswith('invoke') and size >= 3:
                        idx = (units[i+1] << 16) | units[i+2] if op < 0x74 else struct.unpack_from('<I', insns, (i+1)*2)[0]
                        m_class, m_proto, m_name = struct.unpack_from('<HHI', data, method_ids_off + idx*8)
                        detail = f" {get_type_desc(m_class)}.{get_string(m_name)}"
                    elif name.startswith(('iget','iput','sget','sput')) and size >= 2:
                        fid = units[i+1]
                        f_class, f_type, f_name = struct.unpack_from('<HHI', data, field_ids_off + fid*8)
                        detail = f" {get_type_desc(f_class)}.{get_string(f_name)}:{get_type_desc(f_type)}"
                    elif name in ('instance-of','const-class','new-instance','check-cast','new-array') and size >= 2:
                        tid = units[i+1]
                        detail = f" {get_type_desc(tid)}"
                    print(f"  {i:04d}: {name}{detail}")
                    i += size
