#!/usr/bin/env python3
"""S76 Lead-1: dooz F-146 upstream producer trace.

Dumps Lg8; class structure from the dooz APK: fields + all methods, then
disassembles target methods with method/field index resolution so the
def-chain of the null receiver v4 at pc=569 can be traced upstream.

Usage:
  python3 s76_g8_disasm.py <apk> [--method a] [--pc 569]
"""
import sys, zipfile, struct

APK = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGET_CLASS = 'Lg8;'
TARGET_METHOD = 'a'
TARGET_CODE_OFF = None  # direct dump mode: disassemble the code_item at this file offset
SHOW_PC = int(sys.argv[sys.argv.index('--pc') + 1]) if '--pc' in sys.argv else 569
if '--method' in sys.argv:
    TARGET_METHOD = sys.argv[sys.argv.index('--method') + 1]
if '--code-off' in sys.argv:
    TARGET_CODE_OFF = int(sys.argv[sys.argv.index('--code-off') + 1], 16 if sys.argv[sys.argv.index('--code-off') + 1].startswith('0x') else 10)

def uleb(data, off):
    result = 0; shift = 0
    while True:
        b = data[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def sleb(data, off):
    result = 0; shift = 0
    while True:
        b = data[off]; off += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80):
            if b & 0x40:
                result -= (1 << shift)
            break
    return result, off

def get_str(dex, idx):
    off = struct.unpack_from('<I', dex['data'], dex['string_ids_off'] + idx * 4)[0]
    n, off = uleb(dex['data'], off)
    end = off
    while dex['data'][end] != 0: end += 1
    return dex['data'][off:end].decode('utf-8', errors='replace')

def get_type(dex, idx):
    si = struct.unpack_from('<I', dex['data'], dex['type_ids_off'] + idx * 4)[0]
    return get_str(dex, si)

def get_field(dex, idx):
    cls_idx, type_idx, name_idx = struct.unpack_from('<HHI', dex['data'], dex['field_ids_off'] + idx * 8)
    return f'{get_type(dex, cls_idx)}->{get_str(dex, name_idx)}:{get_type(dex, type_idx)}'

def get_method(dex, idx):
    cls_idx, proto_idx, name_idx = struct.unpack_from('<HHI', dex['data'], dex['method_ids_off'] + idx * 8)
    # proto
    po = dex['proto_ids_off'] + proto_idx * 12
    shorty_idx, ret_idx, params_off = struct.unpack_from('<III', dex['data'], po)
    params = []
    if params_off:
        n = struct.unpack_from('<I', dex['data'], params_off)[0]
        o = params_off + 4
        for i in range(n):
            ti = struct.unpack_from('<H', dex['data'], o + i * 2)[0]
            params.append(get_type(dex, ti))
    return f'{get_type(dex, cls_idx)}->{get_str(dex, name_idx)}({"".join(params)}){get_type(dex, ret_idx)}'

# ---- opcode sizes (16-bit code units), exact Dalvik table ----
_S1 = set(range(0x01, 0x0e)) | {0x0e,0x0f,0x10,0x11,0x12,0x1d,0x1e,0x21,0x26,0x27} \
    | set(range(0x7b, 0x90)) | set(range(0xb0, 0xd0))   # move..move-exception, returns, const/4, monitors, array-length, throw, goto, unop, binop/2addr
_S2 = {0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x28} \
    | set(range(0x2c, 0x32)) | set(range(0x32, 0x38)) | set(range(0x38, 0x3e)) \
    | set(range(0x44, 0x70))                            # const/16..goto/16, cmp, if*, aget/aput, iget/iput, sget/sput(0x60..0x6d)
_S3 = {0x14,0x17,0x1b,0x24,0x25,0x29,0x2a,0x2b,0xfc,0xfd} \
    | set(range(0x6e, 0x73)) | set(range(0x74, 0x79))   # const, const-wide/32, jumbo string, filled-new-array, fill-array, goto/32, switch, invoke*, invoke/range
_S5 = {0x18}
_S4 = {0xfa, 0xfb}

def op_size(op):
    if op in _S1: return 1
    if op in _S2: return 2
    if op in _S3: return 3
    if op in _S4: return 4
    if op in _S5: return 5
    return 2  # unused opcode slots — conservative

def decode(dex, code, pc):
    op = code[2 * pc]
    aa = code[2 * pc + 1]
    def h16(o): return struct.unpack_from('<H', code, 2 * o)[0]
    def i32(o): return struct.unpack_from('<i', code, 2 * o)[0]
    name, size, extra = f'op-0x{op:02x}', op_size(op), ''
    if op == 0x54: name, size = 'iget-object', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x5b: name, size = 'iput-object', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x59: name, size = 'iput', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x5a: name, size = 'iput-wide', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x52: name, size = 'iget', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x53: name, size = 'iget-wide', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op == 0x55: name, size = 'iget-boolean', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_field(dex, h16(pc+1))}'
    elif op in (0x6e,0x6f,0x70,0x71,0x72):
        names = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface'}
        name = names[op]; size = 3
        cnt = (aa >> 4) & 0xF
        regs = [f'v{aa & 0xF}'] if cnt == 1 else []
        if cnt > 1:
            # 35c: register list packed in following halfword(s)
            regs = [f'v{(h16(pc+2) >> (4 * i)) & 0xF}' for i in range(cnt)]
        extra = f'{", ".join(regs)}, {get_method(dex, h16(pc+1))}'
    elif op in (0x74,0x75,0x76,0x77,0x78):
        names = {0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range'}
        name = names[op]; size = 3
        cnt = aa
        first = h16(pc + 2)
        extra = f'v{first}..v{first + cnt - 1}, {get_method(dex, h16(pc+1))}'
    elif op == 0x0c: name, size = 'move-result-object', 1; extra = f'v{aa & 0xF}'
    elif op == 0x0a: name, size = 'move-result', 1; extra = f'v{aa & 0xF}'
    elif op == 0x0b: name, size = 'move-result-wide', 1; extra = f'v{aa & 0xF}'
    elif op == 0x07: name, size = 'move-object', 1; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}'
    elif op == 0x08: name, size = 'move-object/from16', 2; extra = f'v{aa & 0xF}, v{h16(pc+1)}'
    elif op == 0x12: name, size = 'const/4', 1; extra = f'v{aa & 0xF}, #int {(aa >> 4) - 16 if (aa >> 4) > 7 else aa >> 4}'
    elif op == 0x13: name, size = 'const/16', 2; extra = f'v{aa & 0xF}, #int {struct.unpack_from("<h", code, 2*(pc+1))[0]}'
    elif op == 0x14: name, size = 'const', 3; extra = f'v{aa & 0xF}, #int {i32(pc+1)}'
    elif op == 0x1a: name, size = 'const-string', 2; extra = f'v{aa & 0xF}, "{get_str(dex, h16(pc+1))}"'
    elif op == 0x22: name, size = 'new-instance', 2; extra = f'v{aa & 0xF}, {get_type(dex, h16(pc+1))}'
    elif op == 0x1f: name, size = 'check-cast', 2; extra = f'v{aa & 0xF}, {get_type(dex, h16(pc+1))}'
    elif op == 0x1c: name, size = 'const-class', 2; extra = f'v{aa & 0xF}, {get_type(dex, h16(pc+1))}'
    elif op in (0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d):
        names = {0x37:'if-eqz',0x38:'if-nez',0x39:'if-ltz',0x3a:'if-gez',0x3b:'if-gtz',0x3c:'if-lez',0x3d:'if-eqz'}
        name = names[op]; size = 2; extra = f'v{aa & 0xF}, ->+{struct.unpack_from("<h", code, 2*(pc+1))[0]}'
    elif op in (0x31,0x32,0x33,0x34,0x35,0x36):
        names = {0x31:'if-eq',0x32:'if-ne',0x33:'if-lt',0x34:'if-ge',0x35:'if-gt',0x36:'if-le'}
        name = names[op]; size = 2
        extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, ->+{struct.unpack_from("<h", code, 2*(pc+1))[0]}'
    elif op == 0x29: name, size = 'goto/32', 3; extra = f'->+{i32(pc+1)}'
    elif op == 0x28: name, size = 'goto/16', 2; extra = f'->+{struct.unpack_from("<h", code, 2*(pc+1))[0]}'
    elif op == 0x27: name, size = 'goto', 1; extra = f'->+{aa - 256 if aa > 127 else aa}'
    elif op == 0x2a: name, size = 'sparse-switch', 3; extra = f'v{aa & 0xF}, @+{i32(pc+1)}'
    elif op == 0x11: name, size = 'return-object', 1; extra = f'v{aa & 0xF}'
    elif op == 0x0f: name, size = 'return', 1; extra = f'v{aa & 0xF}'
    elif op == 0x10: name, size = 'return-wide', 1; extra = f'v{aa & 0xF}'
    elif op == 0x0e: name, size = 'return-void', 1
    elif op == 0x21: name, size = 'array-length', 1; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}'
    elif op == 0x0d: name, size = 'move-exception', 1; extra = f'v{aa & 0xF}'
    elif op == 0x23: name, size = 'new-array', 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, {get_type(dex, h16(pc+1))}'
    elif op in (0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
        names = {0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short'}
        name = names[op]; size = 2; extra = f'v{aa & 0xF}, {get_field(dex, h16(pc+1))}'
    elif 0x7b <= op <= 0x8f:
        names = {0x7b:'int-to-byte',0x7c:'int-to-char',0x7d:'int-to-short',0x7e:'add-int/2addr',0x7f:'sub-int/2addr',0x80:'mul-int/2addr',0x81:'div-int/2addr',0x82:'rem-int/2addr',0x83:'and-int/2addr',0x84:'or-int/2addr',0x85:'xor-int/2addr',0x86:'shl-int/2addr',0x87:'shr-int/2addr',0x88:'ushr-int/2addr',0x89:'add-long/2addr',0x8a:'sub-long/2addr',0x8b:'mul-long/2addr',0x8c:'div-long/2addr',0x8d:'rem-long/2addr',0x8e:'and-long/2addr',0x8f:'or-long/2addr'}
        if op == 0x90: name = 'xor-long/2addr'
        elif op == 0x91: name = 'shl-long/2addr'
        elif op == 0x92: name = 'shr-long/2addr'
        elif op == 0x93: name = 'ushr-long/2addr'
        elif op in (0x94,0x95,0x96,0x97): name = ['add-float/2addr','sub-float/2addr','mul-float/2addr','div-float/2addr'][op-0x94]
        elif op in (0x98,0x99): name = ['rem-float/2addr','add-double/2addr'][op-0x98]
        elif op in (0x9a,0x9b,0x9c,0x9d): name = ['sub-double/2addr','mul-double/2addr','div-double/2addr','rem-double/2addr'][op-0x9a]
        elif op in (0x7e,0x7f,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88) or True: name = names.get(op, f'unop-0x{op:02x}')
        name = names.get(op, name); size = 1; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}' if op >= 0x7e else f'v{aa & 0xF}'
    elif 0xb0 <= op <= 0xcf:
        base = {0xb0:'add-int',0xb1:'sub-int',0xb2:'mul-int',0xb3:'div-int',0xb4:'rem-int',0xb5:'and-int',0xb6:'or-int',0xb7:'xor-int',0xb8:'shl-int',0xb9:'shr-int',0xba:'ushr-int',0xbb:'add-long',0xbc:'sub-long',0xbd:'mul-long',0xbe:'div-long',0xbf:'rem-long',0xc0:'and-long',0xc1:'or-long',0xc2:'xor-long',0xc3:'shl-long',0xc4:'shr-long',0xc5:'ushr-long',0xc6:'add-float',0xc7:'sub-float',0xc8:'mul-float',0xc9:'div-float',0xca:'rem-float',0xcb:'add-double',0xcc:'sub-double',0xcd:'mul-double',0xce:'div-double',0xcf:'rem-double'}
        name = f'{base[op]}/2addr'; size = 1; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}'
    elif op in (0x01,0x04): name = {0x01:'move',0x04:'move-wide'}[op]; size = 1; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}'
    elif op == 0x02: name, size = 'move/from16', 2; extra = f'v{aa & 0xF}, v{h16(pc+1)}'
    elif op == 0x05: name, size = 'move-wide/from16', 2; extra = f'v{aa & 0xF}, v{h16(pc+1)}'
    elif op in (0x2c,0x2d,0x2e,0x2f,0x30,0x31):
        names = {0x2c:'cmpl-float',0x2d:'cmpg-float',0x2e:'cmpl-double',0x2f:'cmpg-double',0x30:'cmp-long',0x31:'NOT-ARRAY-LEN'}
        name = names[op] if op != 0x31 else 'cmp-long'; size = 2
        extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, v{h16(pc+1) & 0xF}'
    elif op == 0x44: name = 'aget'
    elif op in range(0x44, 0x52):
        anames = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short'}
        name = anames[op]; size = 2; extra = f'v{aa & 0xF}, v{(aa >> 4) & 0xF}, v{h16(pc+1) & 0xF}'
    return name, size, extra

def dump_code_item(dex, data, code_off):
    co = code_off
    regs, ins, outs, tries, dbg_off = struct.unpack_from('<HHHHI', data, co)
    units = struct.unpack_from('<I', data, co + 12)[0]
    code = data[co + 16: co + 16 + units * 2]
    print(f'    registers_size={regs} ins={ins} outs={outs} insns={units} units')
    pc = 0
    while pc < units:
        try:
            name_, size_, extra_ = decode(dex, code, pc)
        except Exception as e:
            raw = struct.unpack_from('<I', code, 2 * pc)[0] if pc + 1 < units else 0
            name_, size_, extra_ = f'??op-0x{code[2*pc]:02x}', op_size(code[2*pc]), f'raw=0x{raw:08x} ({e.__class__.__name__})'
        mark = '  <<<< SITE' if pc == SHOW_PC else ''
        print(f'    pc={pc:5d} (0x{pc:03x}) {name_:26s} {extra_}{mark}')
        if size_ <= 0: size_ = 1
        pc += size_

def main():
    with zipfile.ZipFile(APK) as z:
        for dex_name in sorted(n for n in z.namelist() if n.endswith('.dex')):
            data = z.read(dex_name)
            dex = {'data': data,
                   'string_ids_off': struct.unpack_from('<I', data, 0x3c)[0], 'string_ids_size': struct.unpack_from('<I', data, 0x38)[0],
                   'type_ids_off': struct.unpack_from('<I', data, 0x44)[0], 'type_ids_size': struct.unpack_from('<I', data, 0x40)[0],
                   'proto_ids_off': struct.unpack_from('<I', data, 0x4c)[0],
                   'field_ids_off': struct.unpack_from('<I', data, 0x54)[0], 'field_ids_size': struct.unpack_from('<I', data, 0x50)[0],
                   'method_ids_off': struct.unpack_from('<I', data, 0x5c)[0], 'method_ids_size': struct.unpack_from('<I', data, 0x58)[0],
                   'class_defs_off': struct.unpack_from('<I', data, 0x64)[0], 'class_defs_size': struct.unpack_from('<I', data, 0x60)[0]}
            if TARGET_CODE_OFF is not None:
                print(f'=== code_item at 0x{TARGET_CODE_OFF:x} in {dex_name} ===')
                dump_code_item(dex, data, TARGET_CODE_OFF)
                return
            for ci in range(dex['class_defs_size']):
                cd_off = dex['class_defs_off'] + ci * 32
                class_idx = struct.unpack_from('<I', data, cd_off)[0]
                class_data_off = struct.unpack_from('<I', data, cd_off + 24)[0]
                if class_data_off == 0: continue
                type_desc = get_type(dex, class_idx)
                if type_desc != TARGET_CLASS: continue
                print(f'=== {TARGET_CLASS} in {dex_name} (class_def #{ci}) ===')
                print(f'super: {get_type(dex, struct.unpack_from("<I", data, cd_off + 8)[0])}')
                o = class_data_off
                sf, o = uleb(data, o); inf, o = uleb(data, o)
                dm, o = uleb(data, o); vm, o = uleb(data, o)
                fields = []
                fidx = 0
                for i in range(sf):
                    fidx, o = uleb(data, o)
                    acc, o = uleb(data, o)
                    fields.append((fidx, acc, 'static'))
                fidx = 0
                for i in range(inf):
                    fidx, o = uleb(data, o)
                    acc, o = uleb(data, o)
                    fields.append((fidx, acc, 'instance'))
                for fidx, acc, kind in fields:
                    print(f'  field {kind}: {get_field(dex, fidx)}')
                print(f'  direct_methods={dm} virtual_methods={vm}')
                midx = 0
                for kind, count in (('direct', dm), ('virtual', vm)):
                    for i in range(count):
                        midx, o = uleb(data, o)
                        acc, o = uleb(data, o)
                        code_off, o = uleb(data, o)
                        mname = get_method(dex, midx)
                        marker = ' <== TARGET' if kind == 'virtual' and get_str(dex, struct.unpack_from('<HHI', data, dex['method_ids_off'] + midx * 8)[2]) == TARGET_METHOD else ''
                        print(f'  {kind} method[{i}]: {mname} acc=0x{acc:x} code_off=0x{code_off:x}{marker}')
                        if code_off == 0 or marker == '': continue
                        # parse code_item
                        co = code_off
                        regs, ins, outs, tries, dbg_off = struct.unpack_from('<HHHHI', data, co)
                        units = struct.unpack_from('<I', data, co + 12)[0]
                        code = data[co + 16: co + 16 + units * 2]
                        print(f'    registers_size={regs} ins={ins} outs={outs} insns={units} units')
                        pc = 0
                        while pc < units:
                            try:
                                name_, size_, extra_ = decode(dex, code, pc)
                            except Exception as e:
                                raw = struct.unpack_from('<I', code, 2 * pc)[0] if pc + 1 < units else 0
                                name_, size_, extra_ = f'??op-0x{code[2*pc]:02x}', op_size(code[2*pc]), f'raw=0x{raw:08x} ({e.__class__.__name__})'
                            mark = '  <<<< F-146 SITE' if pc == SHOW_PC else ''
                            print(f'    pc={pc:5d} (0x{pc:03x}) {name_:26s} {extra_}{mark}')
                            if size_ <= 0: size_ = 1
                            pc += size_
                return
    print(f'{TARGET_CLASS}: NOT FOUND')

if __name__ == '__main__':
    main()
