#!/usr/bin/env python3
"""
EXP-059 Phase 1: Disassemble ActionBarLayout.addFragmentToStack and related methods.

Dumps raw bytecode + resolves method/field/string/type references for any
method in any DEX file inside the Telegram APK.
"""
import zipfile, struct, sys, os

APK = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'

# AOSP-standard format → size (in 16-bit code units)
FORMAT_SIZE = {
    '10x': 1, '10t': 1, '11x': 1, '11n': 1, '12x': 1,
    '20t': 2, '21s': 2, '21h': 2, '21c': 2, '21t': 2, '22x': 2,
    '22b': 2, '22s': 2, '22c': 2, '22t': 2, '23x': 2,
    '30t': 3, '31i': 3, '31t': 3, '31c': 3, '32x': 3,
    '35c': 3, '3rc': 3, '3rms': 3,
    '51l': 5,
}

# opcode → (mnemonic, format)
OPCODES = {
    0x00: ('nop', '10x'), 0x01: ('move', '12x'), 0x02: ('move/from16', '22x'),
    0x03: ('move/16', '32x'), 0x04: ('move-wide', '12x'), 0x05: ('move-wide/from16', '22x'),
    0x06: ('move-wide/16', '32x'), 0x07: ('move-object', '12x'), 0x08: ('move-object/from16', '22x'),
    0x09: ('move-object/16', '32x'), 0x0a: ('move-result', '11x'), 0x0b: ('move-result-wide', '11x'),
    0x0c: ('move-result-object', '11x'), 0x0d: ('move-exception', '11x'),
    0x0e: ('return-void', '10x'), 0x0f: ('return', '11x'), 0x10: ('return-wide', '11x'),
    0x11: ('return-object', '11x'), 0x12: ('const/4', '11n'), 0x13: ('const/16', '21s'),
    0x14: ('const', '31i'), 0x15: ('const/high16', '21h'),
    0x16: ('const-wide/16', '21s'), 0x17: ('const-wide/32', '21i'),
    0x18: ('const-wide', '51l'), 0x19: ('const-wide/high16', '21h'),
    0x1a: ('const-string', '21c'), 0x1b: ('const-string/jumbo', '31c'),
    0x1c: ('const-class', '21c'), 0x1d: ('monitor-enter', '11x'), 0x1e: ('monitor-exit', '11x'),
    0x1f: ('check-cast', '21c'), 0x20: ('instance-of', '22c'), 0x21: ('array-length', '12x'),
    0x22: ('new-instance', '21c'), 0x23: ('new-array', '22c'), 0x24: ('filled-new-array', '35c'),
    0x25: ('fill-array-data', '31t'), 0x26: ('throw', '11x'),
    0x27: ('goto', '10t'), 0x28: ('goto/16', '20t'), 0x29: ('goto/32', '30t'),
    0x2a: ('packed-switch', '31t'), 0x2b: ('sparse-switch', '31t'),
    0x2c: ('cmpl-float', '23x'), 0x2d: ('cmpg-float', '23x'),
    0x2e: ('cmpl-double', '23x'), 0x2f: ('cmpg-double', '23x'), 0x30: ('cmp-long', '23x'),
    0x31: ('if-eq', '22t'), 0x32: ('if-ne', '22t'),
    0x33: ('if-lt', '22t'), 0x34: ('if-ge', '22t'), 0x35: ('if-gt', '22t'), 0x36: ('if-le', '22t'),
    0x37: ('if-eqz', '21t'), 0x38: ('if-nez', '21t'),
    0x39: ('if-ltz', '21t'), 0x3a: ('if-gez', '21t'), 0x3b: ('if-gtz', '21t'), 0x3c: ('if-lez', '21t'),
    0x44: ('aget', '23x'), 0x45: ('aget-wide', '23x'), 0x46: ('aget-object', '23x'),
    0x47: ('aget-boolean', '23x'), 0x48: ('aget-byte', '23x'), 0x49: ('aget-char', '23x'),
    0x4a: ('aget-short', '23x'),
    0x4b: ('aput', '23x'), 0x4c: ('aput-wide', '23x'), 0x4d: ('aput-object', '23x'),
    0x4e: ('aput-boolean', '23x'), 0x4f: ('aput-byte', '23x'), 0x50: ('aput-char', '23x'),
    0x51: ('aput-short', '23x'),
    0x52: ('iget', '22c'), 0x53: ('iget-wide', '22c'), 0x54: ('iget-object', '22c'),
    0x55: ('iget-boolean', '22c'), 0x56: ('iget-byte', '22c'), 0x57: ('iget-char', '22c'),
    0x58: ('iget-short', '22c'),
    0x59: ('iput', '22c'), 0x5a: ('iput-wide', '22c'), 0x5b: ('iput-object', '22c'),
    0x5c: ('iput-boolean', '22c'), 0x5d: ('iput-byte', '22c'), 0x5e: ('iput-char', '22c'),
    0x5f: ('iput-short', '22c'),
    0x60: ('sget', '21c'), 0x61: ('sget-wide', '21c'), 0x62: ('sget-object', '21c'),
    0x63: ('sget-boolean', '21c'), 0x64: ('sget-byte', '21c'), 0x65: ('sget-char', '21c'),
    0x66: ('sget-short', '21c'),
    0x67: ('sput', '21c'), 0x68: ('sput-wide', '21c'), 0x69: ('sput-object', '21c'),
    0x6a: ('sput-boolean', '21c'), 0x6b: ('sput-byte', '21c'), 0x6c: ('sput-char', '21c'),
    0x6d: ('sput-short', '21c'),
    0x6e: ('invoke-virtual', '35c'), 0x6f: ('invoke-super', '35c'), 0x70: ('invoke-direct', '35c'),
    0x71: ('invoke-static', '35c'), 0x72: ('invoke-interface', '35c'),
    0x74: ('invoke-virtual/range', '3rc'), 0x75: ('invoke-super/range', '3rc'),
    0x76: ('invoke-direct/range', '3rc'), 0x77: ('invoke-static/range', '3rc'),
    0x78: ('invoke-interface/range', '3rc'),
    0x7b: ('neg-int', '12x'), 0x7c: ('not-int', '12x'),
    0x7d: ('neg-long', '12x'), 0x7e: ('not-long', '12x'),
    0x7f: ('neg-float', '12x'), 0x80: ('neg-double', '12x'),
    0x81: ('int-to-long', '12x'), 0x82: ('int-to-float', '12x'), 0x83: ('int-to-double', '12x'),
    0x84: ('long-to-int', '12x'), 0x85: ('long-to-float', '12x'), 0x86: ('long-to-double', '12x'),
    0x87: ('float-to-int', '12x'), 0x88: ('float-to-long', '12x'), 0x89: ('float-to-double', '12x'),
    0x8a: ('double-to-int', '12x'), 0x8b: ('double-to-long', '12x'), 0x8c: ('double-to-float', '12x'),
    0x8d: ('int-to-byte', '12x'), 0x8e: ('int-to-char', '12x'), 0x8f: ('int-to-short', '12x'),
    0x90: ('add-int', '23x'), 0x91: ('sub-int', '23x'), 0x92: ('mul-int', '23x'),
    0x93: ('div-int', '23x'), 0x94: ('rem-int', '23x'),
    0x95: ('and-int', '23x'), 0x96: ('or-int', '23x'), 0x97: ('xor-int', '23x'),
    0x98: ('shl-int', '23x'), 0x99: ('shr-int', '23x'), 0x9a: ('ushr-int', '23x'),
    0x9b: ('add-long', '23x'), 0x9c: ('sub-long', '23x'), 0x9d: ('mul-long', '23x'),
    0x9e: ('div-long', '23x'), 0x9f: ('rem-long', '23x'),
    0xa0: ('and-long', '23x'), 0xa1: ('or-long', '23x'), 0xa2: ('xor-long', '23x'),
    0xa3: ('shl-long', '23x'), 0xa4: ('shr-long', '23x'), 0xa5: ('ushr-long', '23x'),
    0xa6: ('add-float', '23x'), 0xa7: ('sub-float', '23x'), 0xa8: ('mul-float', '23x'),
    0xa9: ('div-float', '23x'), 0xaa: ('rem-float', '23x'),
    0xab: ('add-double', '23x'), 0xac: ('sub-double', '23x'), 0xad: ('mul-double', '23x'),
    0xae: ('div-double', '23x'), 0xaf: ('rem-double', '23x'),
    0xb0: ('add-int/2addr', '12x'), 0xb1: ('sub-int/2addr', '12x'), 0xb2: ('mul-int/2addr', '12x'),
    0xb3: ('div-int/2addr', '12x'), 0xb4: ('rem-int/2addr', '12x'),
    0xb5: ('and-int/2addr', '12x'), 0xb6: ('or-int/2addr', '12x'), 0xb7: ('xor-int/2addr', '12x'),
    0xb8: ('shl-int/2addr', '12x'), 0xb9: ('shr-int/2addr', '12x'), 0xba: ('ushr-int/2addr', '12x'),
    0xbb: ('add-long/2addr', '12x'), 0xbc: ('sub-long/2addr', '12x'), 0xbd: ('mul-long/2addr', '12x'),
    0xbe: ('div-long/2addr', '12x'), 0xbf: ('rem-long/2addr', '12x'),
    0xc0: ('and-long/2addr', '12x'), 0xc1: ('or-long/2addr', '12x'), 0xc2: ('xor-long/2addr', '12x'),
    0xc3: ('shl-long/2addr', '12x'), 0xc4: ('shr-long/2addr', '12x'), 0xc5: ('ushr-long/2addr', '12x'),
    0xc6: ('add-float/2addr', '12x'), 0xc7: ('sub-float/2addr', '12x'), 0xc8: ('mul-float/2addr', '12x'),
    0xc9: ('div-float/2addr', '12x'), 0xca: ('rem-float/2addr', '12x'),
    0xcb: ('add-double/2addr', '12x'), 0xcc: ('sub-double/2addr', '12x'), 0xcd: ('mul-double/2addr', '12x'),
    0xce: ('div-double/2addr', '12x'), 0xcf: ('rem-double/2addr', '12x'),
    0xd0: ('add-int/lit16', '22s'), 0xd1: ('rsub-int', '22s'),
    0xd2: ('mul-int/lit16', '22s'), 0xd3: ('div-int/lit16', '22s'), 0xd4: ('rem-int/lit16', '22s'),
    0xd5: ('and-int/lit16', '22s'), 0xd6: ('or-int/lit16', '22s'), 0xd7: ('xor-int/lit16', '22s'),
    0xd8: ('add-int/lit8', '22b'), 0xd9: ('rsub-int/lit8', '22b'), 0xda: ('mul-int/lit8', '22b'),
    0xdb: ('div-int/lit8', '22b'), 0xdc: ('rem-int/lit8', '22b'),
    0xdd: ('and-int/lit8', '22b'), 0xde: ('or-int/lit8', '22b'), 0xdf: ('xor-int/lit8', '22b'),
    0xe0: ('shl-int/lit8', '22b'), 0xe1: ('shr-int/lit8', '22b'), 0xe2: ('ushr-int/lit8', '22b'),
    0xfa: ('invoke-polymorphic', '35c'), 0xfb: ('invoke-polymorphic/range', '3rc'),
    0xfc: ('invoke-custom', '35c'), 0xfd: ('invoke-custom/range', '3rc'),
    0xfe: ('const-method-handle', '21c'), 0xff: ('const-method-type', '21c'),
}

def load_dex(data):
    return {
        'data': data,
        'string_ids_size': struct.unpack_from('<I', data, 0x38)[0],
        'string_ids_off': struct.unpack_from('<I', data, 0x3c)[0],
        'type_ids_size': struct.unpack_from('<I', data, 0x40)[0],
        'type_ids_off': struct.unpack_from('<I', data, 0x44)[0],
        'proto_ids_size': struct.unpack_from('<I', data, 0x48)[0],
        'proto_ids_off': struct.unpack_from('<I', data, 0x4c)[0],
        'field_ids_size': struct.unpack_from('<I', data, 0x50)[0],
        'field_ids_off': struct.unpack_from('<I', data, 0x54)[0],
        'method_ids_size': struct.unpack_from('<I', data, 0x58)[0],
        'method_ids_off': struct.unpack_from('<I', data, 0x5c)[0],
        'class_defs_size': struct.unpack_from('<I', data, 0x60)[0],
        'class_defs_off': struct.unpack_from('<I', data, 0x64)[0],
    }

def get_string(dex, idx):
    data = dex['data']
    sid_off = dex['string_ids_off'] + idx * 4
    data_off = struct.unpack_from('<I', data, sid_off)[0]
    l = data_off
    while data[l] & 0x80: l += 1
    l += 1
    e = l
    while data[e] != 0: e += 1
    return data[l:e].decode('utf-8', errors='replace')

def get_type(dex, idx):
    data = dex['data']
    type_desc_off = dex['type_ids_off'] + idx * 4
    type_str_idx = struct.unpack_from('<I', data, type_desc_off)[0]
    return get_string(dex, type_str_idx)

def get_proto(dex, idx):
    data = dex['data']
    p_off = dex['proto_ids_off'] + idx * 12
    shorty_idx, ret_type_idx, params_off = struct.unpack_from('<III', data, p_off)
    shorty = get_string(dex, shorty_idx)
    ret_type = get_type(dex, ret_type_idx)
    params = []
    if params_off != 0:
        n = struct.unpack_from('<I', data, params_off)[0]
        for i in range(n):
            t_idx = struct.unpack_from('<H', data, params_off + 4 + i*2)[0]
            params.append(get_type(dex, t_idx))
    return f'{ret_type}({", ".join(params)}) [shorty={shorty}]'

def get_field(dex, idx):
    data = dex['data']
    f_off = dex['field_ids_off'] + idx * 8
    class_idx, type_idx, name_idx = struct.unpack_from('<HHI', data, f_off)
    return f'{get_type(dex, class_idx)}.{get_string(dex, name_idx)} : {get_type(dex, type_idx)}'

def get_method(dex, idx):
    data = dex['data']
    m_off = dex['method_ids_off'] + idx * 8
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', data, m_off)
    return f'{get_type(dex, class_idx)}.{get_string(dex, name_idx)} {get_proto(dex, proto_idx)}'

def uleb(data, off):
    r = 0; sh = 0
    while True:
        b = data[off]; off += 1
        r |= (b & 0x7f) << sh
        sh += 7
        if not (b & 0x80): break
    return r, off

def find_method(dex, target_class, target_method, target_proto_idx=None):
    """Return (code_off, registers_size, ins_size, outs_size, tries_size, debug_off) for matching method."""
    data = dex['data']
    for ci in range(dex['class_defs_size']):
        cd_off = dex['class_defs_off'] + ci * 32
        class_idx = struct.unpack_from('<I', data, cd_off)[0]
        class_data_off = struct.unpack_from('<I', data, cd_off + 24)[0]
        if class_data_off == 0: continue
        if get_type(dex, class_idx) != target_class: continue
        # Parse class_data_item
        p = class_data_off
        sf, p = uleb(data, p)
        if_, p = uleb(data, p)
        dm, p = uleb(data, p)
        vm, p = uleb(data, p)
        # Skip static fields
        f_idx = 0
        for i in range(sf):
            diff, p = uleb(data, p); _, p = uleb(data, p); f_idx += diff
        # Skip instance fields
        f_idx = 0
        for i in range(if_):
            diff, p = uleb(data, p); _, p = uleb(data, p); f_idx += diff
        # Direct methods
        m_idx = 0
        for i in range(dm):
            diff, p = uleb(data, p); access, p = uleb(data, p); code_off, p = uleb(data, p)
            m_idx += diff
            m_off = dex['method_ids_off'] + m_idx * 8
            ci2, pi2, ni2 = struct.unpack_from('<HHI', data, m_off)
            mname = get_string(dex, ni2)
            if mname == target_method and (target_proto_idx is None or pi2 == target_proto_idx):
                if code_off != 0:
                    regs, ins, outs, tries_size, debug_off, insns_size = struct.unpack_from('<HHHHII', data, code_off)
                    return (code_off + 16, regs, ins, outs, tries_size, insns_size)
        # Virtual methods
        m_idx = 0
        for i in range(vm):
            diff, p = uleb(data, p); access, p = uleb(data, p); code_off, p = uleb(data, p)
            m_idx += diff
            m_off = dex['method_ids_off'] + m_idx * 8
            ci2, pi2, ni2 = struct.unpack_from('<HHI', data, m_off)
            mname = get_string(dex, ni2)
            if mname == target_method and (target_proto_idx is None or pi2 == target_proto_idx):
                if code_off != 0:
                    regs, ins, outs, tries_size, debug_off, insns_size = struct.unpack_from('<HHHHII', data, code_off)
                    return (code_off + 16, regs, ins, outs, tries_size, insns_size)
    return None

def disasm(dex, code_off, insns_size):
    data = dex['data']
    pc = 0
    out = []
    while pc < insns_size:
        op = data[2*(code_off//2 + pc)]  # high byte first
        # actually DEX is little-endian: each 16-bit code unit, low byte = opcode
        cu_off = code_off + 2 * pc
        unit = struct.unpack_from('<H', data, cu_off)[0]
        op = unit & 0xff
        high = (unit >> 8) & 0xff
        if op not in OPCODES:
            out.append(f'  PC={pc:5d}  op=0x{op:02x}  unknown')
            pc += 1
            continue
        mnem, fmt = OPCODES[op]
        sz = FORMAT_SIZE[fmt]
        # Decode operands
        extra = ''
        if fmt == '10t':  # goto
            off = struct.unpack_from('<b', data, cu_off + 1)[0]
            extra = f'+{off} → PC={pc+off}'
        elif fmt == '20t':
            off = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'+{off} → PC={pc+off}'
        elif fmt == '30t':
            off = struct.unpack_from('<i', data, cu_off + 2)[0]
            extra = f'+{off} → PC={pc+off}'
        elif fmt == '11n':
            v = high & 0xf
            imm = struct.unpack_from('<b', data, cu_off + 1)[0]
            extra = f'v{v}, #{imm}'
        elif fmt == '11x':
            v = high
            extra = f'v{v}'
        elif fmt == '12x':
            v1 = high & 0xf
            v2 = (high >> 4) & 0xf
            extra = f'v{v1}, v{v2}'
        elif fmt == '21s':
            v = high
            imm = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'v{v}, #{imm}'
        elif fmt == '21h':
            v = high
            imm = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'v{v}, #0x{(imm & 0xffff):04x}'
        elif fmt == '21c':
            v = high
            idx = struct.unpack_from('<H', data, cu_off + 2)[0]
            if op in (0x1c, 0x1f, 0x20, 0x22, 0x23):
                # const-class / check-cast / instance-of / new-instance / new-array
                extra = f'v{v}, {get_type(dex, idx)}'
            elif op >= 0x60 and op <= 0x6d:
                # sget/sput
                extra = f'v{v}, {get_field(dex, idx)}'
            else:
                extra = f'v{v}, idx={idx}'
        elif fmt == '21t':
            v = high
            off = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'v{v}, +{off} → PC={pc+off}'
        elif fmt == '22t':
            v1 = high & 0xf
            v2 = (high >> 4) & 0xf
            off = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'v{v1}, v{v2}, +{off} → PC={pc+off}'
        elif fmt == '22c':
            v1 = high & 0xf
            v2 = (high >> 4) & 0xf
            idx = struct.unpack_from('<H', data, cu_off + 2)[0]
            if op in (0x20, 0x22, 0x23):
                extra = f'v{v1}, v{v2}, {get_type(dex, idx)}'
            elif op >= 0x52 and op <= 0x5f:
                extra = f'v{v1}, v{v2}, {get_field(dex, idx)}'
            else:
                extra = f'v{v1}, v{v2}, idx={idx}'
        elif fmt == '22x':
            v1 = high
            v2 = struct.unpack_from('<H', data, cu_off + 2)[0]
            extra = f'v{v1}, v{v2}'
        elif fmt == '23x':
            v1 = high
            unit2 = struct.unpack_from('<H', data, cu_off + 2)[0]
            v2 = unit2 & 0xff
            v3 = (unit2 >> 8) & 0xff
            extra = f'v{v1}, v{v2}, v{v3}'
        elif fmt == '22s':
            v1 = high & 0xf
            v2 = (high >> 4) & 0xf
            imm = struct.unpack_from('<h', data, cu_off + 2)[0]
            extra = f'v{v1}, v{v2}, #{imm}'
        elif fmt == '22b':
            v1 = high & 0xf
            v2 = (high >> 4) & 0xf
            imm = struct.unpack_from('<b', data, cu_off + 3)[0]
            extra = f'v{v1}, v{v2}, #{imm}'
        elif fmt == '31i':
            v = high
            imm = struct.unpack_from('<i', data, cu_off + 2)[0]
            extra = f'v{v}, #0x{(imm & 0xffffffff):08x}'
        elif fmt == '31c':
            v = high
            idx = struct.unpack_from('<I', data, cu_off + 2)[0]
            extra = f'v{v}, "{get_string(dex, idx)}"'
        elif fmt == '31t':
            v = high
            off = struct.unpack_from('<i', data, cu_off + 2)[0]
            extra = f'v{v}, +{off} → PC={pc+off}'
        elif fmt == '32x':
            v1 = struct.unpack_from('<H', data, cu_off + 2)[0]
            v2 = struct.unpack_from('<H', data, cu_off + 4)[0]
            extra = f'v{v1}, v{v2}'
        elif fmt == '35c':
            arg_count = (high >> 4) & 0xf
            idx = struct.unpack_from('<H', data, cu_off + 2)[0]
            unit3 = struct.unpack_from('<H', data, cu_off + 4)[0]
            vC = high & 0xf
            vD = (unit3 >> 12) & 0xf
            vE = (unit3 >> 8) & 0xf
            vF = (unit3 >> 4) & 0xf
            vG = unit3 & 0xf
            regs = []
            if arg_count == 1: regs = [vC]
            elif arg_count == 2: regs = [vC, vD]
            elif arg_count == 3: regs = [vC, vD, vE]
            elif arg_count == 4: regs = [vC, vD, vE, vF]
            elif arg_count == 5: regs = [vC, vD, vE, vF, vG]
            if op in range(0x6e, 0x73) or op == 0xfa or op == 0xfc:
                extra = f'{{{", ".join(f"v{r}" for r in regs)}}}, {get_method(dex, idx)}'
            elif op == 0x1a:
                extra = f'{{{", ".join(f"v{r}" for r in regs)}}}, "{get_string(dex, idx)}"'
            elif op == 0x24:
                extra = f'{{{", ".join(f"v{r}" for r in regs)}}}, {get_type(dex, idx)}'
            else:
                extra = f'{{{", ".join(f"v{r}" for r in regs)}}}, idx={idx}'
        elif fmt == '3rc':
            arg_count = (high >> 4) & 0xf
            idx = struct.unpack_from('<H', data, cu_off + 2)[0]
            first_reg = struct.unpack_from('<H', data, cu_off + 4)[0]
            regs = [f'v{first_reg}..v{first_reg+arg_count-1}'] if arg_count > 0 else []
            if op in range(0x74, 0x79):
                extra = f'{{{", ".join(regs)}}}, {get_method(dex, idx)}'
            else:
                extra = f'{{{", ".join(regs)}}}, idx={idx}'
        elif fmt == '51l':
            v = high
            imm = struct.unpack_from('<q', data, cu_off + 2)[0]
            extra = f'v{v}, #0x{(imm & 0xffffffffffffffff):016x}'
        out.append(f'  PC={pc:5d}  {mnem:25s}  {extra}')
        pc += sz
    return '\n'.join(out)

def main():
    if len(sys.argv) < 3:
        print('Usage: exp059_disasm.py <class> <method> [proto_idx]')
        print('Example: exp059_disasm.py "Lorg/telegram/ui/ActionBar/ActionBarLayout;" addFragmentToStack 15381')
        sys.exit(1)
    target_class = sys.argv[1]
    target_method = sys.argv[2]
    target_proto_idx = int(sys.argv[3]) if len(sys.argv) > 3 else None
    with zipfile.ZipFile(APK) as z:
        for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
            data = z.read(dex_name)
            dex = load_dex(data)
            # Find method
            result = find_method(dex, target_class, target_method, target_proto_idx)
            if result is None: continue
            code_off, regs, ins, outs, tries, insns_size = result
            print(f'=== {target_class}.{target_method} proto={target_proto_idx} ===')
            print(f'DEX: {dex_name}')
            print(f'registers_size={regs} ins_size={ins} outs_size={outs} tries_size={tries} insns_size={insns_size}')
            print(f'code_off=0x{code_off:x}')
            print('--- bytecode ---')
            print(disasm(dex, code_off, insns_size))
            return
    print(f'NOT FOUND: {target_class}.{target_method}')

if __name__ == '__main__':
    main()
