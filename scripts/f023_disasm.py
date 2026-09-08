#!/usr/bin/env python3
"""F-023 disassembler: dump a method's DEX bytecode with decoded strings,
fields, method refs, and try/catch ranges. Independent oracle (JADX-style),
does not reuse the runtime parser.

Usage: python3 f023_disasm.py <apk> <class-desc> <method-name> [--all]
  --all = dump ALL methods of the class.
"""
import struct, zipfile, sys

apk = sys.argv[1]
target_class = sys.argv[2]
target_method = sys.argv[3] if len(sys.argv) > 3 else None
DUMP_ALL = (len(sys.argv) > 4 and sys.argv[4] == '--all')

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
OPS_2_23x = {op: f'array-op-0x{op:02x}' for op in range(0x44, 0x52)}
OPS_2_23x.update({op: f'binop-0x{op:02x}' for op in range(0x91, 0xa7)})
OPS_2_22b = {op: f'binop/lit16-0x{op:02x}' for op in range(0xd0, 0xd8)}
OPS_2_22b.update({op: f'binop/lit8-0x{op:02x}' for op in range(0xd8, 0xe3)})
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

data = None
dex = {}

def uleb(off):
    result = 0; shift = 0
    while True:
        b = data[off]; off += 1
        result |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80): break
    return result, off

def get_str(idx):
    sid_off = dex['string_ids_off'] + idx * 4
    data_off = struct.unpack_from('<I', data, sid_off)[0]
    lstart = data_off
    while data[lstart] & 0x80: lstart += 1
    lstart += 1
    end = lstart
    while data[end] != 0: end += 1
    return data[lstart:end].decode('utf-8', errors='replace')

def get_type(idx):
    type_desc_off = dex['type_ids_off'] + idx * 4
    type_str_idx = struct.unpack_from('<I', data, type_desc_off)[0]
    return get_str(type_str_idx)

def get_field(idx):
    f_off = dex['field_ids_off'] + idx * 8
    class_idx = struct.unpack_from('<H', data, f_off)[0]
    type_idx = struct.unpack_from('<H', data, f_off + 2)[0]
    name_idx = struct.unpack_from('<I', data, f_off + 4)[0]
    return f'{get_type(class_idx)}.{get_str(name_idx)}:{get_type(type_idx)}'

def get_method(idx):
    m_off = dex['method_ids_off'] + idx * 8
    class_idx = struct.unpack_from('<H', data, m_off)[0]
    name_idx = struct.unpack_from('<I', data, m_off + 4)[0]
    return f'{get_type(class_idx)}.{get_str(name_idx)}'

def decode_op(op, pc):
    cu = struct.unpack_from('<H', data, dex['insns_off'] + pc * 2)[0]
    if op in OPS_1: return OPS_1[op], 1, ''
    if op in OPS_2_12x: return OPS_2_12x[op], 1, f'v{(cu >> 8) & 0xF}, v{cu >> 12}'
    if op in OPS_2_22x:
        a = data[dex['insns_off'] + pc*2 + 1]
        b = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_2_22x[op], 2, f'v{a & 0xF}, v{b}'
    if op in OPS_3_32x:
        a = data[dex['insns_off'] + pc*2 + 1]
        b = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_3_32x[op], 3, f'v{a & 0xF}, v{b}'
    if op in OPS_2_21:
        if op == 0x1c:
            return OPS_2_21[op], 2, f'v{cu >> 8}, {get_type(struct.unpack_from("<H", data, dex["insns_off"] + pc*2 + 2)[0])}'
        return OPS_2_21[op], 2, f'v{cu >> 8}, #0x{struct.unpack_from("<h", data, dex["insns_off"] + pc*2 + 2)[0]}'
    if op in OPS_2_22:
        b = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_2_22[op], 2, f'v{cu & 0xF}, v{(cu >> 4) & 0xF}, ->{pc + b}'
    if op in OPS_2_22c:
        b = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_2_22c[op], 2, f'v{cu & 0xF}, v{(cu >> 4) & 0xF}, {get_field(b)}'
    if op in OPS_2_23x:
        bb = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_2_23x[op], 2, f'v{bb & 0xF}, v{(bb >> 4) & 0xF}, v{(bb >> 8) & 0xF}'
    if op in OPS_2_22b:
        bb = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_2_22b[op], 2, f'v{bb & 0xF}, v{(bb >> 4) & 0xF}, #{(bb >> 8) & 0xFF if bb < 0x8000 else (bb >> 8) - 256}'
    if op == 0x1a:
        sidx = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        return 'const-string', 2, f'v{cu >> 8}, "{get_str(sidx)}"'
    if op in OPS_3_35c:
        # format 35c: AG|op BBBB FEDC  (3 code units)
        arg_count = (cu >> 12) & 0xF
        g = (cu >> 8) & 0xF
        cccc = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        fedc = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 4)[0]
        c = fedc & 0xF; d = (fedc >> 4) & 0xF; e = (fedc >> 8) & 0xF; f = (fedc >> 12) & 0xF
        regmap = [c, d, e, f, g]
        regs = regmap[:arg_count]
        regs_str = ','.join(f'v{r}' for r in regs)
        return OPS_3_35c[op], 3, f'{{{regs_str}}}, {get_method(cccc)}'
    if op in OPS_3_3rc:
        b1 = data[dex['insns_off'] + pc*2 + 1]
        arg_count = (b1 >> 4) & 0xF
        cccc = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 2)[0]
        first = struct.unpack_from('<H', data, dex['insns_off'] + pc*2 + 4)[0]
        return OPS_3_3rc[op], 3, f'{{v{first}..v{first+arg_count-1}}}, {get_method(cccc)}'
    if op in OPS_3_31i:
        val = struct.unpack_from('<i', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_3_31i[op], 3, f'v{data[dex["insns_off"] + pc*2 + 1] & 0xF}, #0x{val & 0xFFFFFFFF:08x}'
    if op in OPS_3_31t:
        offset = struct.unpack_from('<i', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_3_31t[op], 3, f'v{data[dex["insns_off"] + pc*2 + 1] & 0xF}, +{offset} -> PC={pc+offset}'
    if op in OPS_3_21c_jumbo:
        sidx = struct.unpack_from('<I', data, dex['insns_off'] + pc*2 + 2)[0]
        return 'const-string/jumbo', 3, f'v{data[dex["insns_off"] + pc*2 + 1] & 0xF}, "{get_str(sidx)}"'
    if op in OPS_5_51i:
        val = struct.unpack_from('<q', data, dex['insns_off'] + pc*2 + 2)[0]
        return OPS_5_51i[op], 5, f'v{data[dex["insns_off"] + pc*2 + 1] & 0xF}, #0x{val & 0xFFFFFFFFFFFFFFFF:016x}'
    return f'unknown-0x{op:02x}', 1, ''

def dump_code(code_off, class_desc, mname, kind, access):
    regs = struct.unpack_from('<H', data, code_off)[0]
    ins = struct.unpack_from('<H', data, code_off + 2)[0]
    outs = struct.unpack_from('<H', data, code_off + 4)[0]
    tries_size = struct.unpack_from('<H', data, code_off + 6)[0]
    insns = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16
    dex['insns_off'] = insns_off
    print(f"=== {class_desc}.{mname} ({kind}, access=0x{access:x}, regs={regs} ins={ins} outs={outs} insns={insns}) ===")
    pc = 0
    while pc < insns:
        op = data[insns_off + pc * 2]
        try:
            name, size, extra = decode_op(op, pc)
        except Exception as e:
            name, size, extra = f'ERR-0x{op:02x}', 1, str(e)
        print(f"  PC={pc:3d} (0x{pc:04x})  op=0x{op:02x}  {name}  {extra}")
        if size == 0:
            print("  # unknown size, stopping"); break
        pc += size
    if tries_size:
        off = insns_off + insns * 2
        if insns & 1: off += 2
        print(f"  --- try items ({tries_size}) ---")
        for t in range(tries_size):
            start = struct.unpack_from('<I', data, off)[0]
            icount = struct.unpack_from('<H', data, off + 4)[0]
            hoff = struct.unpack_from('<H', data, off + 6)[0]
            print(f"  try[{t}]: start=PC {start} insn_count={icount} handler_off=+{hoff}")
            off += 8
        # handlers (leb-encoded) — decode sizes at least
        hoff_base = off
        sz, p = uleb(off)
        print(f"  handlers: sized={sz} (raw at 0x{p:x})")

with zipfile.ZipFile(apk) as z:
    for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
        data = z.read(dex_name)
        dex = {
            'string_ids_off': struct.unpack_from('<I', data, 0x3c)[0],
            'type_ids_off':   struct.unpack_from('<I', data, 0x44)[0],
            'field_ids_off':  struct.unpack_from('<I', data, 0x54)[0],
            'method_ids_off': struct.unpack_from('<I', data, 0x5c)[0],
            'class_defs_off': struct.unpack_from('<I', data, 0x64)[0],
            'class_defs_size': struct.unpack_from('<I', data, 0x60)[0],
        }
        for ci in range(dex['class_defs_size']):
            cd_off = dex['class_defs_off'] + ci * 32
            class_idx = struct.unpack_from('<I', data, cd_off)[0]
            class_data_off = struct.unpack_from('<I', data, cd_off + 24)[0]
            if class_data_off == 0: continue
            if get_type(class_idx) != target_class: continue
            sf, off = uleb(class_data_off)
            iff, off = uleb(off)
            dm, off = uleb(off)
            vm, off = uleb(off)
            prev = 0
            for _ in range(sf): _, off = uleb(off); _, off = uleb(off)
            prev = 0
            for _ in range(iff): _, off = uleb(off); _, off = uleb(off)
            for kind, count in [('direct', dm), ('virtual', vm)]:
                prev = 0
                for _ in range(count):
                    diff, off = uleb(off); prev += diff
                    access, off = uleb(off)
                    code_off, off = uleb(off)
                    if code_off == 0: continue
                    mname = get_str(struct.unpack_from('<I', data, dex['method_ids_off'] + prev * 8 + 4)[0])
                    if DUMP_ALL or mname == target_method:
                        dump_code(code_off, target_class, mname, kind, access)
