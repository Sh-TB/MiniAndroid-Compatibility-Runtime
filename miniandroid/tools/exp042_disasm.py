#!/usr/bin/env python3
"""Proper Dalvik disassembler — handles multi-unit instructions correctly."""
import sys, zipfile, struct

apk = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
target = sys.argv[1] if len(sys.argv) > 1 else 'Theme.getColor'

# (op, name, num_code_units, format_id)
OPS = {
    0x00: ('nop', 1, '10x'), 0x01: ('move', 1, '12x'), 0x02: ('move/from16', 2, '22x'),
    0x03: ('move/16', 3, '32x'), 0x04: ('move-wide', 1, '12x'), 0x05: ('move-wide/from16', 2, '22x'),
    0x06: ('move-wide/16', 3, '32x'), 0x07: ('move-object', 1, '12x'), 0x08: ('move-object/from16', 2, '22x'),
    0x09: ('move-object/16', 3, '32x'),
    0x0a: ('move-result', 1, '11x'), 0x0b: ('move-result-wide', 1, '11x'),
    0x0c: ('move-result-object', 1, '11x'), 0x0d: ('move-exception', 1, '11x'),
    0x0e: ('return-void', 1, '10x'), 0x0f: ('return', 1, '11x'), 0x10: ('return-wide', 1, '11x'),
    0x11: ('return-object', 1, '11x'),
    0x12: ('const/4', 1, '11n'), 0x13: ('const/16', 2, '21s'), 0x14: ('const', 3, '21i'),
    0x15: ('const/high16', 2, '21h'),
    0x16: ('const-wide/16', 2, '21s'), 0x17: ('const-wide/32', 2, '21i'),
    0x18: ('const-wide', 5, '51i'), 0x19: ('const-wide/high16', 2, '21h'),
    0x1a: ('const-string', 2, '21c'), 0x1b: ('const-string/jumbo', 3, '21c'),
    0x1c: ('const-class', 2, '21c'),
    0x1d: ('monitor-enter', 1, '11x'), 0x1e: ('monitor-exit', 1, '11x'),
    0x1f: ('check-cast', 2, '21c'), 0x20: ('instance-of', 2, '22c'),
    0x21: ('array-length', 1, '12x'), 0x22: ('new-instance', 2, '21c'), 0x23: ('new-array', 2, '22c'),
    0x24: ('filled-new-array', 3, '35c'), 0x25: ('fill-array-data', 3, '31i'), 0x26: ('throw', 1, '11x'),
    0x27: ('goto', 1, '10t'), 0x28: ('goto/16', 2, '20t'), 0x29: ('goto/32', 3, '30t'),
    0x2a: ('packed-switch', 3, '31t'), 0x2b: ('sparse-switch', 3, '31t'),
    0x2c: ('cmpl-float', 2, '23x'), 0x2d: ('cmpg-float', 2, '23x'),
    0x2e: ('cmpl-double', 2, '23x'), 0x2f: ('cmpg-double', 2, '23x'),
    0x30: ('cmp-long', 2, '23x'),
    0x31: ('if-eq', 2, '22t'), 0x32: ('if-ne', 2, '22t'),
    0x33: ('if-lt', 2, '22t'), 0x34: ('if-ge', 2, '22t'),
    0x35: ('if-gt', 2, '22t'), 0x36: ('if-le', 2, '22t'),
    0x37: ('if-eqz', 2, '21t'), 0x38: ('if-nez', 2, '21t'),
    0x39: ('if-ltz', 2, '21t'), 0x3a: ('if-gez', 2, '21t'),
    0x3b: ('if-gtz', 2, '21t'), 0x3c: ('if-lez', 2, '21t'),
    0x44: ('aget', 2, '23x'), 0x45: ('aget-wide', 2, '23x'), 0x46: ('aget-object', 2, '23x'),
    0x47: ('aget-boolean', 2, '23x'), 0x48: ('aget-byte', 2, '23x'),
    0x49: ('aget-char', 2, '23x'), 0x4a: ('aget-short', 2, '23x'),
    0x4b: ('aput', 2, '23x'), 0x4c: ('aput-wide', 2, '23x'), 0x4d: ('aput-object', 2, '23x'),
    0x4e: ('aput-boolean', 2, '23x'), 0x4f: ('aput-byte', 2, '23x'),
    0x50: ('aput-char', 2, '23x'), 0x51: ('aput-short', 2, '23x'),
    0x52: ('iget', 2, '22c'), 0x53: ('iget-wide', 2, '22c'), 0x54: ('iget-object', 2, '22c'),
    0x55: ('iget-boolean', 2, '22c'), 0x56: ('iget-byte', 2, '22c'),
    0x57: ('iget-char', 2, '22c'), 0x58: ('iget-short', 2, '22c'),
    0x59: ('iput', 2, '22c'), 0x5a: ('iput-wide', 2, '22c'), 0x5b: ('iput-object', 2, '22c'),
    0x5c: ('iput-boolean', 2, '22c'), 0x5d: ('iput-byte', 2, '22c'),
    0x5e: ('iput-char', 2, '22c'), 0x5f: ('iput-short', 2, '22c'),
    0x60: ('sget', 2, '21c'), 0x61: ('sget-wide', 2, '21c'), 0x62: ('sget-object', 2, '21c'),
    0x63: ('sget-boolean', 2, '21c'), 0x64: ('sget-byte', 2, '21c'),
    0x65: ('sget-char', 2, '21c'), 0x66: ('sget-short', 2, '21c'),
    0x67: ('sput', 2, '21c'), 0x68: ('sput-wide', 2, '21c'), 0x69: ('sput-object', 2, '21c'),
    0x6a: ('sput-boolean', 2, '21c'), 0x6b: ('sput-byte', 2, '21c'),
    0x6c: ('sput-char', 2, '21c'), 0x6d: ('sput-short', 2, '21c'),
    0x6e: ('invoke-virtual', 3, '35c'), 0x6f: ('invoke-super', 3, '35c'),
    0x70: ('invoke-direct', 3, '35c'), 0x71: ('invoke-static', 3, '35c'),
    0x72: ('invoke-interface', 3, '35c'),
    0x74: ('invoke-virtual/range', 3, '3rc'), 0x75: ('invoke-super/range', 3, '3rc'),
    0x76: ('invoke-direct/range', 3, '3rc'), 0x77: ('invoke-static/range', 3, '3rc'),
    0x78: ('invoke-interface/range', 3, '3rc'),
    0x7b: ('neg-int', 1, '12x'), 0x7c: ('not-int', 1, '12x'),
    0x7d: ('neg-long', 1, '12x'), 0x7e: ('not-long', 1, '12x'),
    0x7f: ('neg-float', 1, '12x'), 0x80: ('neg-double', 1, '12x'),
    0x81: ('int-to-long', 1, '12x'), 0x82: ('int-to-float', 1, '12x'), 0x83: ('int-to-double', 1, '12x'),
    0x84: ('long-to-int', 1, '12x'), 0x85: ('long-to-float', 1, '12x'), 0x86: ('long-to-double', 1, '12x'),
    0x87: ('float-to-int', 1, '12x'), 0x88: ('float-to-long', 1, '12x'), 0x89: ('float-to-double', 1, '12x'),
    0x8a: ('double-to-int', 1, '12x'), 0x8b: ('double-to-long', 1, '12x'), 0x8c: ('double-to-float', 1, '12x'),
    0x8d: ('int-to-byte', 1, '12x'), 0x8e: ('int-to-char', 1, '12x'), 0x8f: ('int-to-short', 1, '12x'),
    0x90: ('add-int', 2, '23x'), 0x91: ('sub-int', 2, '23x'), 0x92: ('mul-int', 2, '23x'),
    0x93: ('div-int', 2, '23x'), 0x94: ('rem-int', 2, '23x'),
    0x95: ('and-int', 2, '23x'), 0x96: ('or-int', 2, '23x'), 0x97: ('xor-int', 2, '23x'),
    0x98: ('shl-int', 2, '23x'), 0x99: ('shr-int', 2, '23x'), 0x9a: ('ushr-int', 2, '23x'),
    0x9b: ('add-long', 2, '23x'), 0x9c: ('sub-long', 2, '23x'), 0x9d: ('mul-long', 2, '23x'),
    0x9e: ('div-long', 2, '23x'), 0x9f: ('rem-long', 2, '23x'),
    0xa0: ('and-long', 2, '23x'), 0xa1: ('or-long', 2, '23x'), 0xa2: ('xor-long', 2, '23x'),
    0xa3: ('shl-long', 2, '23x'), 0xa4: ('shr-long', 2, '23x'), 0xa5: ('ushr-long', 2, '23x'),
    0xa6: ('add-float', 2, '23x'), 0xa7: ('sub-float', 2, '23x'), 0xa8: ('mul-float', 2, '23x'),
    0xa9: ('div-float', 2, '23x'), 0xaa: ('rem-float', 2, '23x'),
    0xab: ('add-double', 2, '23x'), 0xac: ('sub-double', 2, '23x'), 0xad: ('mul-double', 2, '23x'),
    0xae: ('div-double', 2, '23x'), 0xaf: ('rem-double', 2, '23x'),
    0xb0: ('add-int/2addr', 1, '12x'), 0xb1: ('sub-int/2addr', 1, '12x'),
    0xb2: ('mul-int/2addr', 1, '12x'), 0xb3: ('div-int/2addr', 1, '12x'),
    0xb4: ('rem-int/2addr', 1, '12x'), 0xb5: ('and-int/2addr', 1, '12x'),
    0xb6: ('or-int/2addr', 1, '12x'), 0xb7: ('xor-int/2addr', 1, '12x'),
    0xb8: ('shl-int/2addr', 1, '12x'), 0xb9: ('shr-int/2addr', 1, '12x'),
    0xba: ('ushr-int/2addr', 1, '12x'),
    0xbb: ('add-long/2addr', 1, '12x'), 0xbc: ('sub-long/2addr', 1, '12x'),
    0xbd: ('mul-long/2addr', 1, '12x'), 0xbe: ('div-long/2addr', 1, '12x'),
    0xbf: ('rem-long/2addr', 1, '12x'), 0xc0: ('and-long/2addr', 1, '12x'),
    0xc1: ('or-long/2addr', 1, '12x'), 0xc2: ('xor-long/2addr', 1, '12x'),
    0xc3: ('shl-long/2addr', 1, '12x'), 0xc4: ('shr-long/2addr', 1, '12x'),
    0xc5: ('ushr-long/2addr', 1, '12x'),
    0xc6: ('add-float/2addr', 1, '12x'), 0xc7: ('sub-float/2addr', 1, '12x'),
    0xc8: ('mul-float/2addr', 1, '12x'), 0xc9: ('div-float/2addr', 1, '12x'),
    0xca: ('rem-float/2addr', 1, '12x'),
    0xcb: ('add-double/2addr', 1, '12x'), 0xcc: ('sub-double/2addr', 1, '12x'),
    0xcd: ('mul-double/2addr', 1, '12x'), 0xce: ('div-double/2addr', 1, '12x'),
    0xcf: ('rem-double/2addr', 1, '12x'),
    0xd0: ('add-int/lit16', 2, '22s'), 0xd1: ('rsub-int', 2, '22s'),
    0xd2: ('mul-int/lit16', 2, '22s'), 0xd3: ('div-int/lit16', 2, '22s'),
    0xd4: ('rem-int/lit16', 2, '22s'), 0xd5: ('and-int/lit16', 2, '22s'),
    0xd6: ('or-int/lit16', 2, '22s'), 0xd7: ('xor-int/lit16', 2, '22s'),
    0xd8: ('add-int/lit8', 2, '22b'), 0xd9: ('rsub-int/lit8', 2, '22b'),
    0xda: ('mul-int/lit8', 2, '22b'), 0xdb: ('and-int/lit8', 2, '22b'),
    0xdc: ('or-int/lit8', 2, '22b'), 0xdd: ('xor-int/lit8', 2, '22b'),
    0xde: ('shl-int/lit8', 2, '22b'), 0xdf: ('shr-int/lit8', 2, '22b'),
    0xe0: ('ushr-int/lit8', 2, '22b'),
}

def disasm(data, code_off, insns_count, max_pcs=30):
    regs, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', data, code_off)
    bcoff = code_off + 16
    pc = 0
    out = []
    while pc < min(insns, max_pcs):
        op_word = struct.unpack_from('<H', data, bcoff + pc*2)[0]
        op = op_word & 0xFF
        high = (op_word >> 8) & 0xFF
        if op in OPS:
            name, units, fmt = OPS[op]
        else:
            name, units, fmt = f'?0x{op:02x}', 1, '??'
        # Decode operands based on format
        operands = []
        if fmt == '10x': pass
        elif fmt == '11x':
            operands.append(f'v{high}')
        elif fmt == '11n':
            a = high & 0xF
            lit = (high >> 4) & 0xF
            if lit & 0x8: lit -= 16  # sign-extend 4-bit
            operands.append(f'v{a}, #{lit}')
        elif fmt == '12x':
            a = high & 0xF
            b = (high >> 4) & 0xF
            operands.append(f'v{a}, v{b}')
        elif fmt == '10t':
            off = struct.unpack_from('<b', bytes([high]))[0]
            operands.append(f'+{off} → PC={pc+off}')
        elif fmt == '20t':
            next_word = struct.unpack_from('<h', data, bcoff + (pc+1)*2)[0]
            operands.append(f'+{next_word} → PC={pc+next_word}')
        elif fmt == '21s':
            next_word = struct.unpack_from('<h', data, bcoff + (pc+1)*2)[0]
            operands.append(f'v{high}, #{next_word}')
        elif fmt == '21c':
            next_word = struct.unpack_from('<H', data, bcoff + (pc+1)*2)[0]
            operands.append(f'v{high}, @{next_word}')
        elif fmt == '22c':
            next_word = struct.unpack_from('<H', data, bcoff + (pc+1)*2)[0]
            a = high & 0xF
            b = (high >> 4) & 0xF
            operands.append(f'v{a}, v{b}, @{next_word}')
        elif fmt == '21t':
            next_word = struct.unpack_from('<h', data, bcoff + (pc+1)*2)[0]
            operands.append(f'v{high}, +{next_word} → PC={pc+next_word}')
        elif fmt == '22t':
            next_word = struct.unpack_from('<h', data, bcoff + (pc+1)*2)[0]
            a = high & 0xF
            b = (high >> 4) & 0xF
            operands.append(f'v{a}, v{b}, +{next_word} → PC={pc+next_word}')
        elif fmt == '23x':
            next_word = struct.unpack_from('<H', data, bcoff + (pc+1)*2)[0]
            a = high
            b = next_word & 0xFF
            c = (next_word >> 8) & 0xFF
            operands.append(f'v{a}, v{b}, v{c}')
        elif fmt == '35c':
            next_word = struct.unpack_from('<H', data, bcoff + (pc+1)*2)[0]
            regs_word = struct.unpack_from('<H', data, bcoff + (pc+2)*2)[0]
            argc = (high >> 4) & 0xF
            fifth = high & 0xF
            regs_list = [regs_word & 0xF, (regs_word>>4)&0xF, (regs_word>>8)&0xF, (regs_word>>12)&0xF, fifth]
            args_str = ', '.join(f'v{r}' for r in regs_list[:argc])
            operands.append(f'{{{args_str}}}, method@{next_word}')
        elif fmt == '3rc':
            next_word = struct.unpack_from('<H', data, bcoff + (pc+1)*2)[0]
            regs_word = struct.unpack_from('<H', data, bcoff + (pc+2)*2)[0]
            operands.append(f'v{high}..v{high+regs_word}, method@{next_word}')
        out.append(f"  PC={pc:3d}  0x{op_word:04x}  {name:25s}  {', '.join(operands)}")
        pc += units
    return '\n'.join(out)

with zipfile.ZipFile(apk) as z:
    for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
        data = z.read(dex_name)
        if data[:4] != b'dex\n': continue
        strings_size = struct.unpack_from('<I', data, 0x38)[0]
        strings_off = struct.unpack_from('<I', data, 0x3C)[0]
        types_size = struct.unpack_from('<I', data, 0x40)[0]
        types_off = struct.unpack_from('<I', data, 0x44)[0]
        methods_size = struct.unpack_from('<I', data, 0x58)[0]
        methods_off = struct.unpack_from('<I', data, 0x5C)[0]
        class_defs_size = struct.unpack_from('<I', data, 0x60)[0]
        class_defs_off = struct.unpack_from('<I', data, 0x64)[0]
        strings = []
        for i in range(strings_size):
            soff = struct.unpack_from('<I', data, strings_off + i*4)[0]
            p = soff; shift = 0; size = 0
            while True:
                b = data[p]; size |= (b & 0x7F) << shift; p += 1
                if (b & 0x80) == 0: break
                shift += 7
            strings.append(data[p:p+size].decode('utf-8', errors='replace'))
        types = []
        for i in range(types_size):
            didx = struct.unpack_from('<I', data, types_off + i*4)[0]
            types.append(strings[didx])
        methods = []
        for i in range(methods_size):
            class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', data, methods_off + i*8)
            methods.append((types[class_idx], strings[name_idx]))
        def read_uleb(p):
            shift = 0; result = 0
            while True:
                b = data[p]; result |= (b & 0x7F) << shift; p += 1
                if (b & 0x80) == 0: break
                shift += 7
            return result, p
        for ci in range(class_defs_size):
            off = class_defs_off + ci*32
            class_idx = struct.unpack_from('<I', data, off)[0]
            class_data_off = struct.unpack_from('<I', data, off + 24)[0]
            if class_data_off == 0 or class_idx >= types_size: continue
            class_desc = types[class_idx]
            short = class_desc.split('/')[-1].rstrip(';')
            p = class_data_off
            sf, p = read_uleb(p); ifld, p = read_uleb(p); dm, p = read_uleb(p); vm, p = read_uleb(p)
            for _ in range(sf + ifld):
                _, p = read_uleb(p); _, p = read_uleb(p)
            method_idx = 0
            for mi in range(dm + vm):
                mid_diff, p = read_uleb(p); af, p = read_uleb(p); code_off, p = read_uleb(p)
                method_idx += mid_diff
                if method_idx >= len(methods): continue
                mclass, mname = methods[method_idx]
                full = f"{class_desc}.{mname}"
                short_full = f"{short}.{mname}"
                if target.lower() in short_full.lower() or target.lower() in full.lower():
                    if code_off == 0:
                        print(f"=== {full} (ABSTRACT/NATIVE) ===\n")
                        continue
                    regs, ins, outs, tries, dbg, insns = struct.unpack_from('<HHHHII', data, code_off)
                    print(f"=== {full} ({dex_name}, access=0x{af:x}, regs={regs} ins={ins} outs={outs} insns={insns}) ===")
                    print(disasm(data, code_off, insns, 50))
                    print()
