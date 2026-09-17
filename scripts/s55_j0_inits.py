#!/usr/bin/env python3
# S55: resolve the method refs inside Lj/j0;.<init> — which <init> overload
# does the no-arg ctor actually invoke (ground truth for the recursion)?
import struct
import zipfile

APK = '/home/z/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def uleb(data, off):
    result = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, off


apk = zipfile.ZipFile(APK)
data = apk.read('classes.dex')
u32 = lambda o: struct.unpack_from('<I', data, o)[0]
u16 = lambda o: struct.unpack_from('<H', data, o)[0]

string_ids_off = u32(0x3C)
type_ids_off = u32(0x44)
proto_ids_off = u32(0x4C)
field_ids_off = u32(0x54)
method_ids_off = u32(0x5C)
method_ids_size = u32(0x58)
class_defs_off = u32(0x64)
class_defs_size = u32(0x60)


def get_str(idx):
    off = u32(string_ids_off + idx * 4)
    _, off = uleb(data, off)
    end = data.index(b'\x00', off)
    return data[off:end].decode('utf-8', 'replace')


def type_str(idx):
    return get_str(u32(type_ids_off + idx * 4))


def proto_str(idx):
    off = proto_ids_off + idx * 12
    shorty = get_str(u32(off))
    ret = type_str(u32(off + 4))
    params_off = u32(off + 8)
    n = u32(params_off)
    params = ''.join(type_str(u16(params_off + 4 + i * 2)) for i in range(n))
    return f"({params}){ret}"


def method_ref(idx):
    off = method_ids_off + idx * 8
    cls = type_str(u16(off))
    proto = proto_str(u16(off + 2))
    name = get_str(u32(off + 4))
    return f"{cls}-> {name}{proto}"


def field_ref(idx):
    off = field_ids_off + idx * 8
    cls = type_str(u16(off))
    typ = type_str(u16(off + 2))
    name = get_str(u32(off + 4))
    return f"{cls}.{name}:{typ}"


# 1) Resolve the interesting method indices
for mi in (13471,) if 13471 < method_ids_size else ():
    print(f"method@{mi} = {method_ref(mi)}")

# 2) Walk j0's class_data and disassemble every <init> with a proper
#    format walk (only the opcodes that actually occur).


def dump_method(cdesc, mname_filter, code_off):
    nreg = u16(code_off)
    nins = u16(code_off + 2)
    insns_size = u32(code_off + 12)
    print(f"\n## {cdesc} {mname_filter} regs={nreg} ins={nins} "
          f"insns={insns_size}")
    pc = 0
    words = [u16(code_off + 16 + i * 2) for i in range(insns_size)]
    while pc < insns_size:
        w = words[pc]
        op = w & 0xFF
        aa = (w >> 8) & 0xFF
        desc = f"pc={pc:3d} op=0x{op:02x}"
        try:
            if op == 0x12:  # const/4 11n
                desc += f" const/4 v{aa & 0xF}, #{(aa >> 4) & 0xF}"
                pc += 1
            elif op == 0x13:  # const/16 21s
                desc += f" const/16 v{aa}, #{words[pc+1]}"
                pc += 2
            elif op == 0x07:  # move-object 12x
                desc += f" move-object v{aa & 0xF}, v{(aa >> 4) & 0xF}"
                pc += 1
            elif op in (0x22,):  # new-instance 21c
                desc += f" new-instance v{aa}, {type_str(words[pc+1])}"
                pc += 2
            elif op in (0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
                names = {0x70: 'invoke-direct', 0x71: 'invoke-static',
                         0x72: 'invoke-interface', 0x74: 'invoke-virtual/range',
                         0x75: 'invoke-super/range',
                         0x76: 'invoke-direct/range',
                         0x77: 'invoke-static/range',
                         0x78: 'invoke-interface/range'}
                # 35c (0x70-0x72) vs 3rc (0x74-0x78)
                if op <= 0x72:
                    argc = (w >> 12) & 0xF
                    midx = words[pc + 1]
                    regs = [f"v{words[pc+2] & 0xF}",
                            f"v{(words[pc+2] >> 4) & 0xF}",
                            f"v{(words[pc+2] >> 8) & 0xF}",
                            f"v{(words[pc+2] >> 12) & 0xF}",
                            f"v{aa & 0xF}"][:argc]
                    desc += f" {names[op]} {{ {', '.join(regs)} }}, " \
                            f"{method_ref(midx)}"
                    pc += 3
                else:
                    cnt = aa
                    midx = words[pc + 1]
                    start = words[pc + 2]
                    desc += f" {names[op]} {{ v{start}..v{start+cnt-1} }}, " \
                            f"{method_ref(midx)}"
                    pc += 3
            elif op == 0x0c:  # move-result-object 11x
                desc += f" move-result-object v{aa}"
                pc += 1
            elif op == 0x38:  # if-nez 21t
                desc += f" if-nez v{aa} -> {pc + words[pc+1]}"
                pc += 2
            elif op == 0x39:  # if-ltz
                desc += f" if-ltz v{aa} -> {pc + words[pc+1]}"
                pc += 2
            elif op == 0x28:  # goto 10t
                desc += f" goto {pc + 1}"
                pc += 1
            elif op == 0x29:  # goto/16 20t
                desc += f" goto/16 {pc + words[pc+1]}"
                pc += 2
            elif op in (0x5b, 0x5c, 0x5a, 0x59, 0x58):  # iput/aput family
                names = {0x5a: 'iput-object', 0x5b: 'iput-object',
                         0x59: 'iput', 0x58: 'iput-wide'}
                desc += f" {names.get(op, 'iput*')} v{aa & 0xF}, " \
                        f"v{(aa >> 4) & 0xF}, {field_ref(words[pc+1])}"
                pc += 2
            elif op == 0x52:  # iget
                desc += f" iget v{aa & 0xF}, v{(aa >> 4) & 0xF}, " \
                        f"{field_ref(words[pc+1])}"
                pc += 2
            elif op == 0x54:  # iget-object
                desc += f" iget-object v{aa & 0xF}, v{(aa >> 4) & 0xF}, " \
                        f"{field_ref(words[pc+1])}"
                pc += 2
            elif op == 0xdd:  # not standard -> print raw
                desc += f" RAW 0x{w:04x}"
                pc += 1
            elif op == 0x0e:  # return-void
                desc += " return-void"
                pc += 1
            elif op == 0x00:  # nop
                desc += " nop"
                pc += 1
            elif op == 0x0f:  # return
                desc += f" return v{aa}"
                pc += 1
            elif op == 0x11:  # return-object
                desc += f" return-object v{aa}"
                pc += 1
            elif op == 0x21:  # throw
                desc += f" throw v{aa}"
                pc += 1
            else:
                desc += f" ? w=0x{w:04x}"
                pc += 1
        except Exception as exc:
            desc += f" (decode error: {exc})"
            pc += 1
        print(desc)


for ci in range(class_defs_size):
    cd = class_defs_off + ci * 32
    if type_str(u32(cd)) != 'Lj/j0;':
        continue
    print(f"j0 super = {type_str(u32(cd + 4))}")
    class_data_off = u32(cd + 24)
    off = class_data_off
    sf, off = uleb(data, off)
    vf_n, off = uleb(data, off)
    dm, off = uleb(data, off)
    vm, off = uleb(data, off)
    for _ in range(sf + vf_n):
        _, off = uleb(data, off)
        _, off = uleb(data, off)
    midx = 0
    for k in range(dm + vm):
        if k == dm:
            midx = 0
        mdiff, off = uleb(data, off)
        access, off = uleb(data, off)
        code_off, off = uleb(data, off)
        midx += mdiff
        mref = method_ref(midx)
        if '-> <init>' in mref and code_off:
            dump_method('Lj/j0;', mref, code_off)
    break
