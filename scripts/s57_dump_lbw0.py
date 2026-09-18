#!/usr/bin/env python3
# S57 R-NEW-344: full method inventory + bytecode dump for Lbw0; (ScatterMap)
# and Lmg1; (helpers) from dooz23 — ground truth for the nextCapacity branch.
import struct
import sys
import zipfile

APK = 'apk_cache/io.github.yamin8000.dooz_23.apk'
WANT = {'Lbw0;', 'Lmg1;'}


def uleb(data, off):
    result = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            break
        shift += 7
    return result, off


def main():
    data = zipfile.ZipFile(APK).read('classes.dex')
    hdr = {k: struct.unpack_from('<I', data, o)[0] for k, o in [
        ('string_ids_size', 0x38), ('string_ids_off', 0x3C),
        ('type_ids_size', 0x40), ('type_ids_off', 0x44),
        ('proto_ids_off', 0x4C), ('field_ids_size', 0x50), ('field_ids_off', 0x54),
        ('method_ids_size', 0x58), ('method_ids_off', 0x5C),
        ('class_defs_size', 0x60), ('class_defs_off', 0x64)]}

    def get_str(idx):
        off = struct.unpack_from('<I', data, hdr['string_ids_off'] + idx * 4)[0]
        _, off = uleb(data, off)
        end = data.index(b'\x00', off)
        return data[off:end].decode('utf-8', errors='replace')

    def type_str(idx):
        return get_str(struct.unpack_from('<I', data, hdr['type_ids_off'] + idx * 4)[0])

    def method_ref(idx):
        off = hdr['method_ids_off'] + idx * 8
        cls_idx = struct.unpack_from('<H', data, off)[0]
        name_idx = struct.unpack_from('<I', data, off + 4)[0]
        return f"{type_str(cls_idx)}->{get_str(name_idx)}"

    def field_ref(idx):
        off = hdr['field_ids_off'] + idx * 8
        cls_idx = struct.unpack_from('<H', data, off)[0]
        type_idx = struct.unpack_from('<H', data, off + 2)[0]
        name_idx = struct.unpack_from('<I', data, off + 4)[0]
        return f"{type_str(cls_idx)}.{get_str(name_idx)}:{type_str(type_idx)}"

    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    list_only = '--list' in sys.argv

    for ci in range(hdr['class_defs_size']):
        cd = hdr['class_defs_off'] + ci * 32
        cdesc = type_str(struct.unpack_from('<I', data, cd)[0])
        if cdesc not in WANT:
            continue
        class_data_off = struct.unpack_from('<I', data, cd + 24)[0]
        off = class_data_off
        sf, off = uleb(data, off)
        inf, off = uleb(data, off)
        dm, off = uleb(data, off)
        vm, off = uleb(data, off)
        for _ in range(sf + inf):  # skip field entries (2 ulebs each)
            _, off = uleb(data, off)
            _, off = uleb(data, off)
        print(f"\n=== CLASS {cdesc} (direct={dm} virtual={vm}) ===")
        midx = 0
        entries = []
        for i in range(dm + vm):
            mdiff, off = uleb(data, off)
            access, off = uleb(data, off)
            code_off, off = uleb(data, off)
            midx += mdiff
            try:
                mname = get_str(struct.unpack_from('<I', data, hdr['method_ids_off'] + midx * 8 + 4)[0])
            except Exception:
                mname = f"midx_{midx}"
            entries.append((midx, mname, access, code_off))
            if i == dm - 1:
                midx = 0  # virtual diff chain restarts at 0
        for midx_, mname, access, code_off in entries:
            if code_off == 0:
                print(f"  {mname} (abstract/native, code_off=0)")
                continue
            regs = struct.unpack_from('<H', data, code_off)[0]
            ins = struct.unpack_from('<H', data, code_off + 2)[0]
            insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
            print(f"  {mname} regs={regs} ins={ins} insns={insns_size}")
            if list_only:
                continue
            if only and mname not in only:
                continue
            dump_code(data, code_off, method_ref, field_ref, mname, cdesc)


OPNAMES = {
    0x00: 'nop', 0x01: 'move', 0x02: 'move/from16', 0x04: 'move-wide',
    0x07: 'move-object', 0x08: 'move-object/from16',
    0x0a: 'move-result', 0x0b: 'move-result-wide', 0x0c: 'move-result-object',
    0x0d: 'move-exception', 0x0e: 'return-void', 0x0f: 'return',
    0x10: 'return-wide', 0x11: 'return-object', 0x12: 'const/4', 0x13: 'const/16',
    0x14: 'const', 0x15: 'const/high16', 0x16: 'const-wide/16', 0x17: 'const-wide/32',
    0x18: 'const-wide', 0x19: 'const-wide/high16', 0x1a: 'const-string',
    0x1b: 'const-string/jumbo', 0x1c: 'const-class', 0x1d: 'monitor-enter',
    0x1e: 'monitor-exit', 0x1f: 'check-cast', 0x20: 'instance-of',
    0x21: 'array-length', 0x22: 'new-instance', 0x23: 'new-array',
    0x24: 'filled-new-array', 0x25: 'filled-new-array/range',
    0x26: 'fill-array-data', 0x27: 'throw', 0x28: 'goto',
    0x29: 'goto/16', 0x2a: 'goto/32', 0x2b: 'packed-switch', 0x2c: 'sparse-switch',
    0x2d: 'cmpl-float', 0x2e: 'cmpg-float', 0x2f: 'cmpl-double', 0x30: 'cmpg-double',
    0x31: 'cmp-long', 0x32: 'if-eq', 0x33: 'if-ne', 0x34: 'if-lt', 0x35: 'if-ge',
    0x36: 'if-gt', 0x37: 'if-le', 0x38: 'if-eqz', 0x39: 'if-nez', 0x3a: 'if-ltz',
    0x3b: 'if-gez', 0x3c: 'if-gtz', 0x3d: 'if-lez',
    0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object', 0x47: 'aget-boolean',
    0x48: 'aget-byte', 0x4b: 'aget-short',
    0x4d: 'aput', 0x4e: 'aput-wide', 0x4f: 'aput-object', 0x50: 'aput-boolean',
    0x51: 'aput-byte', 0x54: 'iget-object', 0x52: 'iget', 0x53: 'iget-wide',
    0x55: 'iget-boolean', 0x59: 'iput', 0x5a: 'iput-wide', 0x5b: 'iput-object',
    0x5c: 'iput-boolean',
    0x5e: 'sget-wide', 0x60: 'sget', 0x62: 'sget-object', 0x66: 'sget-boolean',
    0x6a: 'sput', 0x6c: 'sput-object', 0x6e: 'invoke-virtual',
    0x6f: 'invoke-super', 0x70: 'invoke-direct', 0x71: 'invoke-static',
    0x72: 'invoke-interface', 0x74: 'invoke-virtual/range', 0x76: 'invoke-direct/range',
    0x77: 'invoke-static/range', 0x78: 'invoke-interface/range',
}


def opsize(op, w):
    # Authoritative DEX opcode size table (16-bit code units)
    if op in (0x01, 0x04, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11,
              0x12, 0x1d, 0x1e, 0x21, 0x27, 0x28) or 0x7b <= op <= 0x8f:
        return 1  # 10x/12x/11n/11x + unary 12x
    if 0xb0 <= op <= 0xcf:
        return 1  # binop/2addr
    if op in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f, 0x20,
              0x22, 0x23, 0x29, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x30, 0x31,
              0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c,
              0x3d) or 0x44 <= op <= 0x6d or 0x90 <= op <= 0xaf or \
            0xd0 <= op <= 0xe2:
        return 2
    if op in (0x03, 0x06, 0x09, 0x14, 0x17, 0x24, 0x25, 0x26, 0x2a, 0x6e, 0x6f,
              0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
        return 3
    if op == 0x18:
        return 5
    if op == 0x00:  # nop / payload
        sub = w >> 8
        if sub == 0x01:
            size = struct.unpack_from('<I', _CODE, _INS + 0)[0] if False else 0
            return 1  # handled in dump (payload skip)
        return 1
    return 1


def dump_code(data, code_off, method_ref, field_ref, mname, cdesc):
    regs = struct.unpack_from('<H', data, code_off)[0]
    insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16
    print(f"\n## {cdesc}->{mname}: regs={regs} insns={insns_size}")
    u16 = [struct.unpack_from('<H', data, insns_off + i * 2)[0] for i in range(insns_size)]
    pc = 0
    while pc < insns_size:
        w = u16[pc]
        op = w & 0xFF
        nx = lambda k: u16[pc + k] if pc + k < insns_size else 0
        line = f"pc={pc:4d} 0x{op:02x}"
        name = OPNAMES.get(op)
        if name is None:
            names = {0x02: 'move/from16', 0x05: 'move-wide/from16', 0x08: 'move-object/from16',
                     0x03: 'move/16', 0x06: 'move-wide/16', 0x09: 'move-object/16',
                     0x7b: 'neg-int', 0x7c: 'not-int', 0x7d: 'neg-long', 0x7e: 'not-long',
                     0x7f: 'neg-float', 0x80: 'neg-double', 0x81: 'int-to-long',
                     0x82: 'int-to-float', 0x83: 'int-to-double', 0x84: 'long-to-int',
                     0x85: 'long-to-float', 0x86: 'long-to-double', 0x87: 'float-to-int',
                     0x88: 'float-to-long', 0x89: 'float-to-double', 0x8a: 'double-to-int',
                     0x8b: 'double-to-long', 0x8c: 'double-to-float', 0x8d: 'int-to-byte',
                     0x8e: 'int-to-char', 0x8f: 'int-to-short',
                     0x90: 'add-int', 0x91: 'sub-int', 0x92: 'mul-int', 0x93: 'div-int',
                     0x94: 'rem-int', 0x95: 'and-int', 0x96: 'or-int', 0x97: 'xor-int',
                     0x98: 'shl-int', 0x99: 'shr-int', 0x9a: 'ushr-int',
                     0x9b: 'add-long', 0x9c: 'sub-long', 0x9d: 'mul-long', 0x9e: 'div-long',
                     0x9f: 'rem-long', 0xa0: 'add-float', 0xa1: 'sub-float',
                     0xa2: 'mul-float', 0xa3: 'div-float', 0xa4: 'rem-float',
                     0xa5: 'add-double', 0xa6: 'sub-double', 0xa7: 'mul-double',
                     0xa8: 'div-double', 0xa9: 'rem-double',
                     0xaa: 'shl-int', 0xab: 'shr-int', 0xac: 'ushr-int',
                     0xad: 'shl-long', 0xae: 'shr-long', 0xaf: 'ushr-long'}
            names.update({0xb0 + i: n + '/2addr' for i, n in enumerate(
                ['add-int', 'sub-int', 'mul-int', 'div-int', 'rem-int', 'and-int',
                 'or-int', 'xor-int', 'shl-int', 'shr-int', 'ushr-int', 'add-long',
                 'sub-long', 'mul-long', 'div-long', 'rem-long', 'add-float',
                 'sub-float', 'mul-float', 'div-float', 'rem-float', 'add-double',
                 'sub-double', 'mul-double', 'div-double', 'rem-double', 'shl-int',
                 'shr-int', 'ushr-int', 'shl-long', 'shr-long', 'ushr-long'])})
            names.update({0xd0: 'add-int/lit16', 0xd1: 'rsub-int', 0xd2: 'mul-int/lit16',
                          0xd3: 'div-int/lit16', 0xd4: 'rem-int/lit16',
                          0xd5: 'and-int/lit16', 0xd6: 'or-int/lit16',
                          0xd7: 'xor-int/lit16', 0xd8: 'add-int/lit8',
                          0xd9: 'rsub-int/lit8', 0xda: 'mul-int/lit8',
                          0xdb: 'div-int/lit8', 0xdc: 'rem-int/lit8',
                          0xdd: 'and-int/lit8', 0xde: 'or-int/lit8',
                          0xdf: 'xor-int/lit8', 0xe0: 'shl-int/lit8',
                          0xe1: 'shr-int/lit8', 0xe2: 'ushr-int/lit8'})
            name = names.get(op, f'op-{op:02x}')
        line += f" {name}"
        # operand rendering per family
        if 0x7b <= op <= 0x8f:  # unary 12x
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}"
        elif op in (0x02, 0x05, 0x08):
            line += f" v{w >> 8 & 0xF}, v{nx(1) & 0xFF}"
        # operand rendering per family
        if op == 0x12:  # const/4
            line += f" v{w >> 8 & 0xF}, {(w >> 12) & 0xF if (w >> 12) & 0xF < 8 else (w >> 12) - 16}"
        elif op in (0x13, 0x16):
            line += f" v{nx(1) & 0xFF}, {nx(1) >> 8}"
        elif op == 0x14:
            line += f" v{nx(1) & 0xFF}, {(nx(2) << 16) | nx(1) >> 8:#x}"
        elif op == 0x15:
            line += f" v{nx(1) & 0xFF}, {nx(1) >> 8:#x}0000"
        elif op in (0x54, 0x52, 0x53, 0x55, 0x59, 0x5a, 0x5b, 0x5c):
            fn = {0x54: 'iget-object', 0x52: 'iget', 0x53: 'iget-wide', 0x55: 'iget-boolean',
                  0x59: 'iput', 0x5a: 'iput-wide', 0x5b: 'iput-object', 0x5c: 'iput-boolean'}[op]
            line = f"pc={pc:4d} 0x{op:02x} {fn} v{w >> 8 & 0xF}, v{w >> 12 & 0xF}, {field_ref(nx(1))}"
        elif op in (0x60, 0x62, 0x5e, 0x66, 0x6a, 0x6c):
            fn = {0x60: 'sget', 0x62: 'sget-object', 0x5e: 'sget-wide', 0x66: 'sget-boolean',
                  0x6a: 'sput', 0x6c: 'sput-object'}[op]
            line = f"pc={pc:4d} 0x{op:02x} {fn} v{nx(1) & 0xFF}, {field_ref(nx(1))}"
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            regs_s = f"v{w >> 12 & 0xF}" if insns_size else ""
            cnt = (w >> 12) & 0xF
            rs = [f"v{(nx(1) >> (4 * i)) & 0xF}" for i in range(cnt)]
            line += f" {{{', '.join(rs)}}}, {method_ref(nx(2))}"
        elif op in (0x74, 0x76, 0x77, 0x78):
            line += f" v{nx(1) & 0xFF}..+{(w >> 8) & 0xFF}, {method_ref(nx(2))}"
        elif 0x32 <= op <= 0x37:
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}, ->{pc + nx(1)}"
        elif 0x38 <= op <= 0x3d:
            line += f" v{w >> 8 & 0xF}, ->{pc + nx(1)}"
        elif op == 0x28:
            line += f" ->{pc + ((w >> 8) & 0xFF if (w >> 8) < 0x80 else (w >> 8) - 256)}"
        elif op == 0x29:
            off16 = nx(1)
            if off16 >= 0x8000:
                off16 -= 0x10000
            line += f" ->{pc + off16}"
        elif op in (0x44, 0x45, 0x46, 0x47, 0x48, 0x4b, 0x4d, 0x4e, 0x4f, 0x50, 0x51):
            fn = {0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object', 0x47: 'aget-boolean',
                  0x4b: 'aget-short', 0x4d: 'aput', 0x4e: 'aput-wide', 0x4f: 'aput-object',
                  0x50: 'aput-boolean', 0x51: 'aput-byte'}[op]
            line = f"pc={pc:4d} 0x{op:02x} {fn} v{w >> 8 & 0xF}, v{w >> 12 & 0xF}, v{nx(1) & 0xFF}"
        elif 0xb0 <= op <= 0xcf:
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}"
        elif 0xd0 <= op <= 0xd7:
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}, {nx(1)}"
        elif 0xd8 <= op <= 0xe2:
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}, {(nx(1) >> 8) & 0xFF if (nx(1) >> 8) < 128 else (nx(1) >> 8) - 256}"
        elif op == 0x22:
            line += f" v{nx(1) & 0xFF}, {type_str(nx(1))}" if False else f" v{nx(1) & 0xFF}, type@{nx(1) >> 8}"
        elif op == 0x1f:
            line += f" v{w >> 8 & 0xF}, type@{nx(1) >> 8}"
        elif op == 0x0f:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x11:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x0c:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x0b:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x0a:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x21:
            line += f" v{w >> 8 & 0xF}, v{w >> 12 & 0xF}"
        elif op == 0x23:
            line += f" v{nx(1) & 0xFF}, v{w >> 8 & 0xF}, type@{nx(1) >> 8}"
        elif op == 0x27:
            line += f" v{w >> 8 & 0xF}"
        elif op == 0x26:
            line += f" v{nx(1) & 0xFF}, ->{pc + (nx(2) if nx(2) < 0x8000 else nx(2) - 0x10000)}"
        elif op == 0x2b or op == 0x2c:
            line += f" v{nx(1) & 0xFF}, ->{pc + (nx(2) if nx(2) < 0x8000 else nx(2) - 0x10000)}"
        print(line)
        pc += opsize(op, w)


if __name__ == '__main__':
    main()
