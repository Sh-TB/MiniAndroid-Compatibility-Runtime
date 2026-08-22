#!/usr/bin/env python3
"""EXP-051: Dump raw bytes of a specific method's bytecode."""
import sys, zipfile, struct

apk = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
target_class = sys.argv[1] if len(sys.argv) > 1 else 'Landroidx/lifecycle/LifecycleRegistry;'
target_method = sys.argv[2] if len(sys.argv) > 2 else 'enforceMainThreadIfNeeded'

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
             0x5d:'iput-byte',0x5e:'iput-char',0x5f:'iput-short',
             0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
             0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',
             0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',
             0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}
OPS_2_23x = {}
for op in range(0x44, 0x52): OPS_2_23x[op] = f'array-op-0x{op:02x}'
for op in range(0x91, 0xa7): OPS_2_23x[op] = f'binop-0x{op:02x}'
OPS_2_22b = {}
for op in range(0xd0, 0xd8): OPS_2_22b[op] = f'binop/lit16-0x{op:02x}'
for op in range(0x9c, 0xa7): OPS_2_22b[op] = f'binop/lit8-0x{op:02x}'
OPS_3_35c = {0x1a:'const-string',0x24:'filled-new-array',
             0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
             0x71:'invoke-static',0x72:'invoke-interface'}
OPS_3_3rc = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',
             0x76:'invoke-direct/range',0x77:'invoke-static/range',
             0x78:'invoke-interface/range'}
OPS_3_31i = {0x14:'const',0x25:'fill-array-data'}
OPS_3_31t = {0x2a:'packed-switch',0x2b:'sparse-switch'}
OPS_3_21c_jumbo = {0x1b:'const-string/jumbo'}
OPS_5_51i = {0x18:'const-wide'}

def decode_op(op, data, pc, dex):
    """Return (name, size, extra_str)."""
    if op in OPS_1: return OPS_1[op], 1, ''
    if op in OPS_2_12x: return OPS_2_12x[op], 1, f'v{(data[2*pc+1] >> 4) & 0xF}, v{data[2*pc+1] & 0xF}'
    if op in OPS_2_22x:
        a = data[2*pc+1]; b = struct.unpack_from('<H', data, 2*pc+2)[0]
        return OPS_2_22x[op], 2, f'v{a & 0xF}, v{b}'
    if op in OPS_3_32x:
        a = data[2*pc+1]
        b = struct.unpack_from('<H', data, 2*pc+2)[0]
        return OPS_3_32x[op], 3, f'v{a & 0xF}, v{b}'
    if op in OPS_2_21:
        if op == 0x28:  # goto/16
            offset = struct.unpack_from('<h', data, 2*pc+2)[0]
            return 'goto/16', 2, f'+{offset} → PC={pc+offset}'
        if op in (0x37,0x38,0x39,0x3a,0x3b,0x3c):  # if-*z
            a = data[2*pc+1] & 0xF
            offset = struct.unpack_from('<h', data, 2*pc+2)[0]
            return OPS_2_21[op], 2, f'v{a}, +{offset} → PC={pc+offset}'
        a = data[2*pc+1]
        val = struct.unpack_from('<h', data, 2*pc+2)[0]
        return OPS_2_21[op], 2, f'v{a & 0xF}, #{val}'
    if op in OPS_2_22:
        if op in (0x31,0x32,0x33,0x34,0x35,0x36):
            byte = data[2*pc+1]
            va = (byte >> 4) & 0xF
            vb = byte & 0xF
            offset = struct.unpack_from('<h', data, 2*pc+2)[0]
            return OPS_2_22[op], 2, f'v{va}, v{vb}, +{offset} → PC={pc+offset}'
    if op in OPS_2_22c:
        byte = data[2*pc+1]
        va = (byte >> 4) & 0xF
        vb = byte & 0xF
        field_idx = struct.unpack_from('<H', data, 2*pc+2)[0]
        return OPS_2_22c[op], 2, f'v{va}, v{vb}, field@{field_idx}'
    if op in OPS_2_23x:
        a = data[2*pc+1]
        b = struct.unpack_from('<H', data, 2*pc+2)[0]
        return OPS_2_23x[op], 2, f'v{a & 0xF}, v{(b>>8)&0xF}, v{b&0xF}'
    if op in OPS_2_22b:
        byte = data[2*pc+1]
        va = (byte >> 4) & 0xF
        vb = byte & 0xF
        lit = struct.unpack_from('<B', data, 2*pc+2)[0]
        # signed
        if lit & 0x80: lit -= 256
        # actually 22b is u8 not s8 for some; check
        return OPS_2_22b[op], 2, f'v{va}, v{vb}, #0x{lit & 0xFF:x}'
    if op in OPS_3_35c:
        byte1 = data[2*pc+1]
        # 35c: (arg_count << 4) | (A), then CCCC, then DDDD
        arg_count = (byte1 >> 4) & 0xF
        a = byte1 & 0xF
        cccc = struct.unpack_from('<H', data, 2*pc+2)[0]
        dddd = struct.unpack_from('<H', data, 2*pc+4)[0]
        # If arg_count == 5, registers are vD, vC, vE, vF, vG
        # If arg_count == 1, register is vD
        # Construct register list:
        regs = []
        if arg_count == 1: regs = [a]
        elif arg_count == 2: regs = [a, (dddd >> 12) & 0xF]
        elif arg_count == 3: regs = [a, (dddd >> 12) & 0xF, (dddd >> 8) & 0xF]
        elif arg_count == 4: regs = [a, (dddd >> 12) & 0xF, (dddd >> 8) & 0xF, (dddd >> 4) & 0xF]
        elif arg_count == 5: regs = [(dddd >> 12) & 0xF, (dddd >> 8) & 0xF, (dddd >> 4) & 0xF, dddd & 0xF, a]
        # resolve method name
        m_off = dex['method_ids_off'] + cccc * 8
        class_idx = struct.unpack_from('<H', data, m_off)[0]
        proto_idx = struct.unpack_from('<H', data, m_off+2)[0]
        name_idx = struct.unpack_from('<I', data, m_off+4)[0]
        # class name
        type_desc_off = dex['type_ids_off'] + class_idx * 4
        type_str_idx = struct.unpack_from('<I', data, type_desc_off)[0]
        # string at type_str_idx
        sid_off = dex['string_ids_off'] + type_str_idx * 4
        data_off = struct.unpack_from('<I', data, sid_off)[0]
        # uleb128 length
        end = data_off
        while data[end] != 0: end += 1
        class_name = data[data_off:end].decode('utf-8', errors='replace')
        # Skip uleb128 length for method name string
        sid_off = dex['string_ids_off'] + name_idx * 4
        data_off = struct.unpack_from('<I', data, sid_off)[0]
        # skip uleb128 length
        lstart = data_off
        while data[lstart] & 0x80: lstart += 1
        lstart += 1
        end = lstart
        while data[end] != 0: end += 1
        mname = data[lstart:end].decode('utf-8', errors='replace')
        regs_str = ','.join(f'v{r}' for r in regs)
        return OPS_3_35c[op], 3, f'{{{regs_str}}}, {class_name}.{mname}'
    if op in OPS_3_3rc:
        byte1 = data[2*pc+1]
        arg_count = (byte1 >> 4) & 0xF
        cccc = struct.unpack_from('<H', data, 2*pc+2)[0]
        first_reg = struct.unpack_from('<H', data, 2*pc+4)[0]
        return OPS_3_3rc[op], 3, f'{{v{first_reg}..v{first_reg+arg_count-1}}}, method@{cccc}'
    if op in OPS_3_31i:
        val = struct.unpack_from('<i', data, 2*pc+2)[0]
        return OPS_3_31i[op], 3, f'v{data[2*pc+1] & 0xF}, #0x{val & 0xFFFFFFFF:08x}'
    if op in OPS_3_31t:
        offset = struct.unpack_from('<i', data, 2*pc+2)[0]
        return OPS_3_31t[op], 3, f'v{data[2*pc+1] & 0xF}, +{offset} → PC={pc+offset}'
    if op in OPS_3_21c_jumbo:
        str_idx = struct.unpack_from('<I', data, 2*pc+2)[0]
        sid_off = dex['string_ids_off'] + str_idx * 4
        data_off = struct.unpack_from('<I', data, sid_off)[0]
        lstart = data_off
        while data[lstart] & 0x80: lstart += 1
        lstart += 1
        end = lstart
        while data[end] != 0: end += 1
        s = data[lstart:end].decode('utf-8', errors='replace')
        return 'const-string/jumbo', 3, f'v{data[2*pc+1] & 0xF}, "{s}"'
    if op in OPS_5_51i:
        val = struct.unpack_from('<q', data, 2*pc+2)[0]
        return OPS_5_51i[op], 5, f'v{data[2*pc+1] & 0xF}, #0x{val & 0xFFFFFFFFFFFFFFFF:016x}'
    return f'unknown-0x{op:02x}', 1, ''

with zipfile.ZipFile(apk) as z:
    for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
        data = z.read(dex_name)
        # Parse header
        dex = {
            'data': data,
            'string_ids_off': struct.unpack_from('<I', data, 0x3c)[0],
            'string_ids_size': struct.unpack_from('<I', data, 0x38)[0],
            'type_ids_off':   struct.unpack_from('<I', data, 0x44)[0],
            'type_ids_size':   struct.unpack_from('<I', data, 0x40)[0],
            'method_ids_off': struct.unpack_from('<I', data, 0x5c)[0],
            'method_ids_size': struct.unpack_from('<I', data, 0x58)[0],
            'class_defs_off': struct.unpack_from('<I', data, 0x64)[0],
            'class_defs_size': struct.unpack_from('<I', data, 0x60)[0],
        }
        # Find class
        for ci in range(dex['class_defs_size']):
            cd_off = dex['class_defs_off'] + ci * 32
            class_idx = struct.unpack_from('<I', data, cd_off)[0]
            class_data_off = struct.unpack_from('<I', data, cd_off + 24)[0]
            if class_data_off == 0: continue
            type_desc_off = dex['type_ids_off'] + class_idx * 4
            type_str_idx = struct.unpack_from('<I', data, type_desc_off)[0]
            sid_off = dex['string_ids_off'] + type_str_idx * 4
            data_off = struct.unpack_from('<I', data, sid_off)[0]
            end = data_off
            while data[end] != 0: end += 1
            class_desc = data[data_off:end].decode('utf-8', errors='replace')
            if class_desc != target_class: continue
            # Parse class_data_item
            def uleb(off):
                result = 0; shift = 0
                while True:
                    b = data[off]; off += 1
                    result |= (b & 0x7F) << shift
                    if not (b & 0x80): break
                    shift += 7
                return result, off
            off = class_data_off
            sf, off = uleb(off)
            iff, off = uleb(off)
            dm, off = uleb(off)
            vm, off = uleb(off)
            # Skip fields
            prev = 0
            for _ in range(sf):
                _, off = uleb(off); _, off = uleb(off)
            prev = 0
            for _ in range(iff):
                _, off = uleb(off); _, off = uleb(off)
            # Parse methods
            for kind, count in [('direct', dm), ('virtual', vm)]:
                prev = 0
                for _ in range(count):
                    diff, off = uleb(off)
                    prev += diff
                    access, off = uleb(off)
                    code_off, off = uleb(off)
                    if code_off == 0: continue
                    # Get method name
                    m_off = dex['method_ids_off'] + prev * 8
                    name_idx = struct.unpack_from('<I', data, m_off + 4)[0]
                    sid_off = dex['string_ids_off'] + name_idx * 4
                    data_off = struct.unpack_from('<I', data, sid_off)[0]
                    lstart = data_off
                    while data[lstart] & 0x80: lstart += 1
                    lstart += 1
                    end = lstart
                    while data[end] != 0: end += 1
                    mname = data[lstart:end].decode('utf-8', errors='replace')
                    if mname != target_method: continue
                    # Found! Parse code_item
                    regs = struct.unpack_from('<H', data, code_off)[0]
                    ins = struct.unpack_from('<H', data, code_off + 2)[0]
                    outs = struct.unpack_from('<H', data, code_off + 4)[0]
                    insns = struct.unpack_from('<I', data, code_off + 12)[0]
                    insns_off = code_off + 16
                    print(f"=== {class_desc}.{mname} ({kind}, access=0x{access:x}, regs={regs} ins={ins} outs={outs} insns={insns}) in {dex_name} ===")
                    pc = 0
                    while pc < insns:
                        op_off = insns_off + pc * 2
                        op = data[op_off]  # low byte only
                        # 16-bit value at this PC
                        cu = struct.unpack_from('<H', data, op_off)[0]
                        name, size, extra = decode_op(op, data, pc, dex)
                        print(f"  PC={pc:3d} (0x{pc:04x})  cu=0x{cu:04x}  op=0x{op:02x}  {name}  {extra}")
                        if size == 0:
                            print("  # unknown size, stopping")
                            break
                        pc += size
                    sys.exit(0)
print(f"# {target_class}.{target_method}: not found")
