#!/usr/bin/env python3
"""
EXP-057 Phase 2: Precise raw DEX disassembly of LaunchActivity.onCreate
using AOSP-standard instruction sizes.

AOSP Dalvik bytecode spec: https://source.android.com/devices/tech/dalvik/dalvik-bytecode

Key: instruction sizes are FIXED by format ID, not by opcode.
The format is determined by the opcode. D8 hybrid goto/16 and goto/32
change the *offset encoding* but NOT the instruction size.

goto (0x27): 10t format, 1 code unit
goto/16 (0x28): 20t format, 2 code units (ALWAYS — D8 hybrid only changes offset encoding)
goto/32 (0x29): 30t format, 3 code units (ALWAYS)

This is critical: previous disassembly attempts used D8 hybrid mode to
change instruction SIZES, which is WRONG. D8 hybrid only changes how the
OFFSET is encoded within the instruction, not how many code units the
instruction occupies.
"""

import zipfile, struct, sys

APK = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'

# AOSP-standard format → size (in 16-bit code units)
# Source: https://source.android.com/devices/tech/dalvik/dalvik-bytecode
FORMAT_SIZE = {
    '10x': 1, '10t': 1, '11x': 1, '11n': 1, '12x': 1,
    '20t': 2, '21s': 2, '21h': 2, '21c': 2, '21t': 2, '22x': 2,
    '22b': 2, '22s': 2, '22c': 2, '22t': 2, '23x': 2,
    '30t': 3, '31i': 3, '31t': 3, '31c': 3, '32x': 3,
    '35c': 3, '3rc': 3, '3rms': 3,
    '51l': 5,
}

# AOSP opcode → (mnemonic, format)
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
    0x6e: ('invoke-virtual', '35c'), 0x6f: ('invoke-super', '35c'),
    0x70: ('invoke-direct', '35c'), 0x71: ('invoke-static', '35c'),
    0x72: ('invoke-interface', '35c'),
    0x74: ('invoke-virtual/range', '3rc'), 0x75: ('invoke-super/range', '3rc'),
    0x76: ('invoke-direct/range', '3rc'), 0x77: ('invoke-static/range', '3rc'),
    0x78: ('invoke-interface/range', '3rc'),
    0x7b: ('neg-un', '12x'), 0x7c: ('neg-int', '12x'), 0x7d: ('not-int', '12x'),
    0x7e: ('neg-long', '12x'), 0x7f: ('not-long', '12x'),
    0x80: ('neg-float', '12x'), 0x81: ('neg-double', '12x'),
    0x82: ('int-to-long', '12x'), 0x83: ('int-to-float', '12x'), 0x84: ('int-to-double', '12x'),
    0x85: ('long-to-int', '12x'), 0x86: ('long-to-float', '12x'), 0x87: ('long-to-double', '12x'),
    0x88: ('float-to-int', '12x'), 0x89: ('float-to-long', '12x'), 0x8a: ('float-to-double', '12x'),
    0x8b: ('double-to-int', '12x'), 0x8c: ('double-to-long', '12x'), 0x8d: ('double-to-float', '12x'),
    0x8e: ('int-to-byte', '12x'), 0x8f: ('int-to-char', '12x'), 0x90: ('int-to-short', '12x'),
    0x91: ('add-int', '23x'), 0x92: ('sub-int', '23x'), 0x93: ('mul-int', '23x'),
    0x94: ('div-int', '23x'), 0x95: ('rem-int', '23x'),
    0x96: ('and-int', '23x'), 0x97: ('or-int', '23x'), 0x98: ('xor-int', '23x'),
    0x99: ('shl-int', '23x'), 0x9a: ('shr-int', '23x'), 0x9b: ('ushr-int', '23x'),
    0x9c: ('add-int/lit8', '22b'), 0x9d: ('rsub-int', '22b'),
    0x9e: ('mul-int/lit8', '22b'), 0x9f: ('div-int/lit8', '22b'),
    0xa0: ('rem-int/lit8', '22b'), 0xa1: ('and-int/lit8', '22b'),
    0xa2: ('or-int/lit8', '22b'), 0xa3: ('xor-int/lit8', '22b'),
    0xa4: ('shl-int/lit8', '22b'), 0xa5: ('shr-int/lit8', '22b'),
    0xa6: ('ushr-int/lit8', '22b'),
    0xd0: ('add-int/lit16', '22s'), 0xd1: ('rsub-int', '22s'),
    0xd2: ('mul-int/lit16', '22s'), 0xd3: ('div-int/lit16', '22s'),
    0xd4: ('rem-int/lit16', '22s'), 0xd5: ('and-int/lit16', '22s'),
    0xd6: ('or-int/lit16', '22s'), 0xd7: ('xor-int/lit16', '22s'),
    0xe0: ('add-int/2addr', '12x'), 0xe1: ('sub-int/2addr', '12x'),
    0xfa: ('invoke-polymorphic', '35c'), 0xfb: ('invoke-polymorphic/range', '3rc'),
    0xfc: ('invoke-custom', '35c'), 0xfd: ('invoke-custom/range', '3rc'),
    0xfe: ('const-method-handle', '21c'), 0xff: ('const-method-type', '21c'),
}

# Extended opcodes (0x00 with sub-opcode in high byte)
EXTENDED = {
    0x00: 'nop',
    0x01: 'packed-switch-payload',
    0x02: 'sparse-switch-payload',
    0x03: 'fill-array-data-payload',
}


def get_size(op):
    """Get instruction size in code units from AOSP spec."""
    if op in OPCODES:
        mnemonic, fmt = OPCODES[op]
        return FORMAT_SIZE.get(fmt, 1)
    return 1


def decode_instruction(data, insns_off, pc, dex_data):
    """Decode a single instruction at the given PC."""
    cu = struct.unpack_from('<H', data, insns_off + pc * 2)[0]
    op = cu & 0xFF
    high = (cu >> 8) & 0xFF

    if op in OPCODES:
        mnemonic, fmt = OPCODES[op]
        size = FORMAT_SIZE.get(fmt, 1)
    else:
        mnemonic = f'unknown-0x{op:02x}'
        fmt = '?'
        size = 1

    # Decode operands based on format
    details = ''
    if fmt == '10x':
        pass  # no operands
    elif fmt == '10t':  # goto: AA|op, AA is signed 8-bit offset
        offset = struct.unpack('<b', bytes([high]))[0]
        details = f'+{offset} → PC={pc + offset}'
    elif fmt == '20t':  # goto/16: op|AAAA, AAAA is signed 16-bit offset
        if pc + 1 < 10000:
            offset = struct.unpack_from('<h', data, insns_off + (pc + 1) * 2)[0]
            details = f'+{offset} → PC={pc + offset}'
        # NOTE: D8 hybrid mode: if high byte != 0, the high byte IS the offset
        # and the instruction is STILL 2 code units (the second unit is a NOP/padding)
        if high != 0:
            d8_offset = struct.unpack('<b', bytes([high]))[0]
            details = f'+{d8_offset} → PC={pc + d8_offset} [D8-hybrid: high={high}]'
    elif fmt == '30t':  # goto/32
        if pc + 2 < 10000:
            lo = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            hi = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
            offset = struct.unpack('<i', struct.pack('<HH', lo, hi))[0]
            details = f'+{offset} → PC={pc + offset}'
        if high != 0:
            d8_offset = struct.unpack('<b', bytes([high]))[0]
            details = f'+{d8_offset} → PC={pc + d8_offset} [D8-hybrid: high={high}]'
    elif fmt == '11x':  # return, move-result, etc: AA|op
        details = f'v{high}'
    elif fmt == '11n':  # const/4: B|A|op, A=dest, B=literal
        A = high & 0xF
        B = (high >> 4) & 0xF
        # B is signed 4-bit
        if B & 0x8: B -= 16
        details = f'v{A}, #{B}'
    elif fmt == '12x':  # move: B|A|op
        A = high & 0xF
        B = (high >> 4) & 0xF
        details = f'v{A}, v{B}'
    elif fmt == '21s':  # const/16: AA|op, #BBBB
        if pc + 1 < 10000:
            val = struct.unpack_from('<h', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, #{val}'
    elif fmt == '21h':  # const/high16: AA|op, #BBBB
        if pc + 1 < 10000:
            val = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, #0x{val:04x}0000'
    elif fmt == '21c':  # const-string, const-class, sget, sput, new-instance, check-cast
        if pc + 1 < 10000:
            idx = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, @{idx}'
    elif fmt == '21t':  # if-*z: AA|op, +BBBB
        if pc + 1 < 10000:
            offset = struct.unpack_from('<h', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, +{offset} → PC={pc + offset}'
    elif fmt == '22t':  # if-*: B|A|op, +CCCC
        if pc + 1 < 10000:
            offset = struct.unpack_from('<h', data, insns_off + (pc + 1) * 2)[0]
            A = high & 0xF
            B = (high >> 4) & 0xF
            details = f'v{A}, v{B}, +{offset} → PC={pc + offset}'
    elif fmt == '22c':  # iget/iput/new-array/instance-of: B|A|op, CCCC
        if pc + 1 < 10000:
            idx = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            A = high & 0xF
            B = (high >> 4) & 0xF
            details = f'v{A}, v{B}, @{idx}'
    elif fmt == '22x':  # move/from16: AA|op, BBBB
        if pc + 1 < 10000:
            src = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, v{src}'
    elif fmt == '22b':  # binop/lit8: AA|op, BB, CC
        if pc + 1 < 10000:
            bb = data[insns_off + (pc + 1) * 2]
            cc = data[insns_off + (pc + 1) * 2 + 1]
            details = f'v{high}, v{bb}, #{cc}'
    elif fmt == '22s':  # binop/lit16: AA|op, BB, CCCC
        if pc + 1 < 10000:
            bb = data[insns_off + (pc + 1) * 2]
            cc = struct.unpack_from('<h', data, insns_off + (pc + 1) * 2)[0]
            # Actually 22s: B|A|op CCCC
            A = high & 0xF
            B = (high >> 4) & 0xF
            details = f'v{A}, v{B}, #{cc}'
    elif fmt == '23x':  # binop: AA|op, BB, CC
        if pc + 1 < 10000:
            bb = data[insns_off + (pc + 1) * 2]
            cc = data[insns_off + (pc + 1) * 2 + 1]
            details = f'v{high}, v{bb}, v{cc}'
    elif fmt == '31i':  # const: AA|op, BBBBBBBB
        if pc + 2 < 10000:
            lo = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            hi = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
            val = struct.unpack('<i', struct.pack('<HH', lo, hi))[0]
            details = f'v{high}, #{val}'
    elif fmt == '31t':  # packed-switch, sparse-switch, fill-array-data
        if pc + 1 < 10000:
            offset = struct.unpack_from('<i', data, insns_off + (pc + 1) * 2)[0]
            details = f'v{high}, +{offset} → PC={pc + offset}'
    elif fmt == '31c':  # const-string/jumbo
        if pc + 2 < 10000:
            lo = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            hi = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
            idx = struct.unpack('<I', struct.pack('<HH', lo, hi))[0]
            details = f'v{high}, string@{idx}'
    elif fmt == '35c':  # invoke-*: A|G|op BBBB FEDC
        if pc + 2 < 10000:
            method_idx = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            regs_word = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
            argc = (high >> 4) & 0xF
            # G = high & 0xF (5th register)
            g = high & 0xF
            regs = []
            if argc >= 1: regs.append(f'v{regs_word & 0xF}')
            if argc >= 2: regs.append(f'v{(regs_word >> 4) & 0xF}')
            if argc >= 3: regs.append(f'v{(regs_word >> 8) & 0xF}')
            if argc >= 4: regs.append(f'v{(regs_word >> 12) & 0xF}')
            if argc >= 5: regs.append(f'v{g}')
            details = f'{{{",".join(regs)}}}, method@{method_idx}'
    elif fmt == '3rc':  # invoke-*/range: AA|op BBBB CCCC
        if pc + 2 < 10000:
            method_idx = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
            first_reg = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
            argc = high
            details = f'{{v{first_reg}..v{first_reg + argc - 1}}}, method@{method_idx}'
    elif fmt == '51l':  # const-wide: AA|op, BBBBBBBB
        b0 = struct.unpack_from('<H', data, insns_off + (pc + 1) * 2)[0]
        b1 = struct.unpack_from('<H', data, insns_off + (pc + 2) * 2)[0]
        b2 = struct.unpack_from('<H', data, insns_off + (pc + 3) * 2)[0]
        b3 = struct.unpack_from('<H', data, insns_off + (pc + 4) * 2)[0]
        val = struct.unpack('<q', struct.pack('<HHHH', b0, b1, b2, b3))[0]
        details = f'v{high}, #{val}L'

    return mnemonic, fmt, size, details, cu


def resolve_method(data, method_idx, dex):
    """Resolve method_idx to class.method string."""
    method_ids_off = dex['method_ids_off']
    string_ids_off = dex['string_ids_off']
    type_ids_off = dex['type_ids_off']
    m_off = method_ids_off + method_idx * 8
    class_idx = struct.unpack_from('<H', data, m_off)[0]
    name_idx = struct.unpack_from('<I', data, m_off + 4)[0]
    t_off = type_ids_off + class_idx * 4
    ts = struct.unpack_from('<I', data, t_off)[0]
    sd = struct.unpack_from('<I', data, string_ids_off + ts * 4)[0]
    p = sd
    while data[p] & 0x80: p += 1
    p += 1
    end = data.index(0, p)
    cn = data[p:end].decode()
    sd2 = struct.unpack_from('<I', data, string_ids_off + name_idx * 4)[0]
    p2 = sd2
    while data[p2] & 0x80: p2 += 1
    p2 += 1
    e2 = data.index(0, p2)
    mn = data[p2:e2].decode()
    return f'{cn}.{mn}'


def main():
    with zipfile.ZipFile(APK) as z:
        data = z.read('classes4.dex')

    dex = {
        'string_ids_off': struct.unpack_from('<I', data, 0x3c)[0],
        'type_ids_off': struct.unpack_from('<I', data, 0x44)[0],
        'method_ids_off': struct.unpack_from('<I', data, 0x5c)[0],
        'class_defs_off': struct.unpack_from('<I', data, 0x64)[0],
        'class_defs_size': struct.unpack_from('<I', data, 0x60)[0],
    }

    # Find LaunchActivity.onCreate
    # From earlier: code_off = 0x523998
    code_off = 0x523998
    insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16

    print(f'LaunchActivity.onCreate: insns_size={insns_size}')
    print(f'=== AOSP-standard disassembly PC 670-740 ===')
    print(f'{"PC":>5}  {"cu":>6}  {"op":>4}  {"mnemonic":<22}  {"fmt":>4}  {"sz":>2}  details')
    print('-' * 100)

    pc = 670
    while pc < 740 and pc < insns_size:
        mnemonic, fmt, size, details, cu = decode_instruction(data, insns_off, pc, dex)

        # Resolve method names for invoke-* instructions
        if 'invoke' in mnemonic and details:
            # Extract method_idx from details
            parts = details.split('method@')
            if len(parts) > 1:
                method_idx = int(parts[1])
                full_name = resolve_method(data, method_idx, dex)
                details = details + f'  → {full_name}'

        print(f'{pc:5d}  0x{cu:04x}  0x{cu & 0xff:02x}  {mnemonic:<22}  {fmt:>4}  {size:2d}  {details}')
        pc += size

    # Also show the region around PC 970 (where execution currently jumps to)
    print(f'\n=== PC 965-985 (current jump target) ===')
    pc = 965
    while pc < 985 and pc < insns_size:
        mnemonic, fmt, size, details, cu = decode_instruction(data, insns_off, pc, dex)
        if 'invoke' in mnemonic and details:
            parts = details.split('method@')
            if len(parts) > 1:
                method_idx = int(parts[1])
                full_name = resolve_method(data, method_idx, dex)
                details = details + f'  → {full_name}'
        print(f'{pc:5d}  0x{cu:04x}  0x{cu & 0xff:02x}  {mnemonic:<22}  {fmt:>4}  {size:2d}  {details}')
        pc += size

    # Also show PC 76-100 (the first isClientActivated call site)
    print(f'\n=== PC 76-100 (first isClientActivated call site) ===')
    pc = 76
    while pc < 100 and pc < insns_size:
        mnemonic, fmt, size, details, cu = decode_instruction(data, insns_off, pc, dex)
        if 'invoke' in mnemonic and details:
            parts = details.split('method@')
            if len(parts) > 1:
                method_idx = int(parts[1])
                full_name = resolve_method(data, method_idx, dex)
                details = details + f'  → {full_name}'
        print(f'{pc:5d}  0x{cu:04x}  0x{cu & 0xff:02x}  {mnemonic:<22}  {fmt:>4}  {size:2d}  {details}')
        pc += size


if __name__ == '__main__':
    main()
