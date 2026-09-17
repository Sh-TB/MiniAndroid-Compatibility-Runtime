#!/usr/bin/env python3
# S56 R-NEW-344 refix recon: dump the HALT-LOOP spin method Lbw0;.d and the
# AIOOBE face Lbw0;.a / Lnb0;.n / Lfb1;.a / Lfb1;.J from dooz v23 — DEX ground
# truth for the await-spin -> garbage-index analysis.
import struct
import sys
import zipfile

APK = 'apk_cache/io.github.yamin8000.dooz_23.apk'
WANT = {'Lbw0;', 'Lnb0;', 'Lfb1;'}


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
        for _ in range(sf + inf):
            _, off = uleb(data, off)
            _, off = uleb(data, off)
        print(f"\n=== CLASS {cdesc} (direct={dm} virtual={vm}) ===")
        midx = 0
        for _ in range(dm + vm):
            mdiff, off = uleb(data, off)
            access, off = uleb(data, off)
            code_off, off = uleb(data, off)
            midx += mdiff
            try:
                mname = get_str(struct.unpack_from('<I', data, hdr['method_ids_off'] + midx * 8 + 4)[0])
            except Exception:
                print(f"  [bad midx={midx} at entry; dm={dm} vm={vm} off={off:#x}]")
                mname = f"midx_{midx}"
            if code_off == 0 or mname not in sys.argv[1:]:
                if _ == dm - 1:
                    midx = 0  # virtual-method diff chain restarts at 0
                continue
            dump_code(data, code_off, method_ref, field_ref, mname, cdesc)
            if _ == dm - 1:
                midx = 0  # virtual-method diff chain restarts at 0


def dump_code(data, code_off, method_ref, field_ref, mname, cdesc):
    regs = struct.unpack_from('<H', data, code_off)[0]
    ins = struct.unpack_from('<H', data, code_off + 2)[0]
    outs = struct.unpack_from('<H', data, code_off + 4)[0]
    insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16
    print(f"\n## {cdesc}->{mname}: regs={regs} ins={ins} outs={outs} insns={insns_size}")
    u16 = [struct.unpack_from('<H', data, insns_off + i * 2)[0] for i in range(insns_size)]
    pc = 0
    while pc < insns_size:
        w = u16[pc]
        op = w & 0xFF
        nx = lambda k: u16[pc + k] if pc + k < insns_size else 0
        line = f"pc={pc:4d} 0x{op:02x}"
        if op == 0x54:
            line += f" iget-object v{(w>>8)&0xF}, v{(w>>12)&0xF}, {field_ref(nx(1))}"
        elif op in (0x52,):
            line += f" iget v{(w>>8)&0xF}, v{(w>>12)&0xF}, {field_ref(nx(1))}"
        elif op in (0x53, 0x5a):
            names = {0x53: 'iget-wide', 0x5a: 'iput-wide'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, {field_ref(nx(1))}"
        elif op in (0x5b, 0x59):
            names = {0x5b: 'iput-object', 0x59: 'iput'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, {field_ref(nx(1))}"
        elif op in (0x60, 0x62):
            names = {0x60: 'sget', 0x62: 'sget-object'}
            line += f" {names[op]} v{(w>>8)&0xF}, {field_ref(nx(1))}"
        elif op in (0x6a, 0x6c):
            names = {0x6a: 'sput', 0x6c: 'sput-object'}
            line += f" {names[op]} v{(w>>8)&0xF}, {field_ref(nx(1))}"
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            names = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super',
                     0x70: 'invoke-direct', 0x71: 'invoke-static',
                     0x72: 'invoke-interface'}
            line += f" {names[op]} {method_ref(nx(1))}"
        elif op == 0x0e:
            line += " return-void"
        elif op == 0x0f:
            line += f" return v{w>>8}"
        elif op == 0x10:
            line += f" return-wide v{w>>8}"
        elif op == 0x11:
            line += f" return-object v{w>>8}"
        elif op == 0x12:
            lit = (w >> 12) & 0xF
            if lit > 7:
                lit -= 16
            line += f" const/4 v{(w>>8)&0xF}, #{lit}"
        elif op == 0x13:
            val = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" const/16 v{(w>>8)&0xF}, #{val}"
        elif op == 0x14:
            val = struct.unpack_from('<i', b''.join(struct.pack('<H', u16[pc+1+k]) for k in range(2)), 0)[0]
            line += f" const v{(w>>8)&0xF}, #{val} (0x{val & 0xFFFFFFFF:08x})"
        elif op == 0x15:
            line += f" const/high16 v{(w>>8)&0xF}, #0x{nx(1):04x}"
        elif op == 0x16:
            val = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" const-wide/16 v{(w>>8)&0xF}, #{val}"
        elif op == 0x17:
            val = struct.unpack_from('<i', b''.join(struct.pack('<H', u16[pc+1+k]) for k in range(2)), 0)[0]
            line += f" const-wide/32 v{(w>>8)&0xF}, #{val}"
        elif op == 0x18:
            val = struct.unpack_from('<q', b''.join(struct.pack('<H', u16[pc+1+k]) for k in range(4)), 0)[0]
            line += f" const-wide v{(w>>8)&0xF}, #{val}"
        elif op == 0x1a:
            line += f" const-string v{(w>>8)&0xF}, \"{get_str(nx(1))[:40]}\""
        elif op in (0x27, 0x28):
            names = {0x27: 'throw', 0x28: 'goto'}
            if op == 0x27:
                line += f" throw v{(w>>8)&0xF}"
            else:
                line += f" goto {(w>>8)&0xFF if (w>>8)&0x80 else (w>>8)&0xFF}"
        elif op in (0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c):
            names = {0x37: 'if-eqz', 0x38: 'if-nez', 0x39: 'if-ltz',
                     0x3a: 'if-gez', 0x3b: 'if-gtz', 0x3c: 'if-lez'}
            line += f" {names[op]} v{(w>>8)&0xF}, +{nx(1)}"
        elif op in (0x31, 0x32, 0x33, 0x34, 0x35, 0x36):
            names = {0x31: 'if-eq', 0x32: 'if-ne', 0x33: 'if-lt',
                     0x34: 'if-ge', 0x35: 'if-gt', 0x36: 'if-le'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, +{nx(1)}"
        elif op in range(0x44, 0x52):
            names = {0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object',
                     0x47: 'aget-boolean', 0x48: 'aget-byte', 0x49: 'aget-char',
                     0x4a: 'aget-short', 0x4b: 'aput', 0x4c: 'aput-wide',
                     0x4d: 'aput-object', 0x4e: 'aput-boolean', 0x4f: 'aput-byte',
                     0x50: 'aput-char', 0x51: 'aput-short'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, v{nx(1)&0xF}"
        elif op in (0x90, 0x9b, 0xa0, 0xa2):
            names = {0x90: 'add-int', 0x9b: 'sub-int', 0xa0: 'add-long', 0xa2: 'sub-long'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, v{nx(1)&0xF}"
        elif op in (0xb0, 0xb1, 0xbb, 0xbf):
            names = {0xb0: 'add-int/2addr', 0xb1: 'sub-int/2addr',
                     0xbb: 'sub-long/2addr', 0xbf: 'xor-long/2addr'}
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}"
        elif op == 0x21:
            line += f" array-length v{(w>>8)&0xF}, v{(w>>12)&0xF}"
        elif op == 0x23:
            line += f" new-array v{(w>>8)&0xF}, v{(w>>12)&0xF}, type@{nx(1)}"
        elif op == 0x0c:
            line += f" move-result-object v{w>>8}"
        elif op == 0x0a:
            line += f" move-result v{w>>8}"
        elif op == 0x0b:
            line += f" move-result-wide v{w>>8}"
        elif op == 0x01:
            line += f" move v{(w>>8)&0xF}, v{(w>>12)&0xF}"
        elif op == 0x07:
            line += f" move-object v{(w>>8)&0xF}, v{(w>>12)&0xF}"
        elif op in (0x02, 0x05, 0x08):
            names = {0x02: 'move/from16', 0x05: 'move-wide/from16', 0x08: 'move-object/from16'}
            line += f" {names[op]} v{w>>8}, v{nx(1)}"
        elif op == 0x22:
            line += f" new-instance v{w>>8}, type@{nx(1)}"
        elif op == 0x1f:
            line += f" check-cast v{w>>8}, type@{nx(1)}"
        elif op in (0xd8, 0xda, 0xdc):
            names = {0xd8: 'add-int/lit8', 0xda: 'mul-int/lit8', 0xdc: 'div-int/lit8'}
            lit = struct.unpack_from('<b', struct.pack('<H', nx(1)), 0)[0] >> 0
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, #{nx(1)&0xFF if lit >= 0 else lit}"
        elif op in (0xd0, 0xd2):
            names = {0xd0: 'add-int/lit16', 0xd2: 'mul-int/lit16'}
            lit = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" {names[op]} v{(w>>8)&0xF}, v{(w>>12)&0xF}, #{lit}"
        elif op == 0x00:
            sub = w >> 8
            line += " nop" if sub == 0 else f" nop/payload({sub})"
            if sub == 0x01:  # packed-switch payload
                size = struct.unpack_from('<I', data, insns_off + (pc + 2) * 2 + 4)[0]
                pc += 2 + (size * 2 + 4) // 2
            elif sub == 0x02:
                size = struct.unpack_from('<I', data, insns_off + (pc + 2) * 2 + 4)[0]
                pc += 2 + (size * 4 + 2) // 2
            elif sub == 0x03:
                size = struct.unpack_from('<I', data, insns_off + (pc + 2) * 2 + 4)[0]
                pc += 2 + (size * 2 + 1)
        print(line)
        pc += opsize(op, w)


def opsize(op, w):
    # Dalvik format sizes (16-bit units)
    if op in (0x00, 0x01, 0x04, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
              0x11, 0x12, 0x1d, 0x1e, 0x27, 0x28):  # 10x/12x/11x/10t
        return 1
    if 0xb0 <= op <= 0xcf:                              # binop/2addr 12x
        return 1
    if op in (0x02, 0x03, 0x05, 0x06, 0x08, 0x09,       # 22x/32x
              0x13, 0x15, 0x16, 0x19,                   # 21s/21h
              0x1a, 0x1c, 0x1f, 0x22,                   # 21c const-string/class/cast/new-inst
              0x20, 0x21, 0x23,                         # 22c/22b-ish
              0x29,                                     # goto/16
              0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,  # sget 21c
              0x6a, 0x6b, 0x6c, 0x6d):                  # sput 21c
        return 2
    if 0x52 <= op <= 0x5f:                              # iget/iput 22c
        return 2
    if 0x32 <= op <= 0x37:                              # if-test 22t
        return 2
    if 0x38 <= op <= 0x3d:                              # if-testz 21t
        return 2
    if 0x44 <= op <= 0x51:                              # aget/aput 23x
        return 2
    if 0x90 <= op <= 0xaf:                              # binop 23x
        return 2
    if 0xd0 <= op <= 0xe2:                              # binop/lit16 + lit8
        return 2
    if op in (0x14, 0x17):                              # const/const-wide-32 31i
        return 3
    if op in (0x1b, 0x26, 0x24, 0x25, 0x2b, 0x2c):      # jumbo-str, fill-array-data,
        return 3                                        # filled-new-array, switch
    if 0x2d <= op <= 0x31:                              # cmp* 23x
        return 2
    if op == 0x18:                                      # const-wide 51l
        return 5
    if op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
        return 3                                        # invoke 35c/3rc
    if op == 0x2a:                                      # goto/32 30t
        return 3
    return 1


if __name__ == '__main__':
    main()
