#!/usr/bin/env python3
"""CONT-11: correct per-method disassembler using the full SIZES table.
Usage: cont11_method_dump.py <Lcls;> <method> [max_pc]
"""
import sys, struct

cls = sys.argv[1] if len(sys.argv) > 1 else 'Landroidx/startup/InitializationProvider;'
mname = sys.argv[2] if len(sys.argv) > 2 else 'onCreate'
maxpc = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9

sys.argv = ['x']
exec(open('/home/z/my-project/scripts/cont11_train1_disasm.py')
     .read().split('def disasm')[0])

import zipfile

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apk'

z = zipfile.ZipFile(APK)
dx = Dex(z.read('classes.dex'))
sup, fields, dm, vm = dx.class_members(cls)
for n, p, co in list(dm) + list(vm):
    if n != mname or not co:
        continue
    regs, ins, midx = dx._read_code(co, 0)
    print(f'=== {cls}.{mname}{p} regs={regs} insns={len(ins)//2} ===')
    u16 = lambda off: struct.unpack_from('<H', ins, off*2)[0]
    pc = 0
    while pc < len(ins)//2 and pc <= maxpc:
        op = ins[pc*2] & 0xFF
        size = SIZES.get(op, 1)
        name = NAMES.get(op, f'op-0x{op:02x}')
        extra = ''
        if op == 0x1a:
            extra = f'"{dx.s(u16(pc+1))[:56]}"'
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
            c, nm, pp = dx.mid(u16(pc+1))
            aa = ins[pc*2+1]
            if op <= 0x72:  # 35c: A|G|op BBBB F|E|D|C — regs C,D,E,F,G
                a_cnt = (aa >> 4) & 0xF
                rs = [ins[pc*2+4] & 0xF, (ins[pc*2+4] >> 4) & 0xF,
                      ins[pc*2+5] & 0xF, (ins[pc*2+5] >> 4) & 0xF,
                      aa & 0xF]
                regs = ",".join(f"v{r}" for r in rs[:a_cnt])
            else:  # 3rc: AA|op BBBB CCCC
                regs = f"{aa}@v{u16(pc+2)}"
            extra = f'{{{regs}}} {c}.{nm}{pp}'
        elif op == 0x22:
            extra = dx.t(u16(pc+1))
        elif op in (0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x5b,
                    0x5c, 0x5d, 0x5e, 0x5f, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
                    0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d):
            c, nm, ty = dx.fid(u16(pc+1))
            extra = f'{c}.{nm}'
        elif op in (0x27,):
            pass
        elif op in (0x28, 0x29) or 0x2d <= op <= 0x3d:
            if op == 0x28:
                d = struct.unpack_from('<h', ins, (pc+1)*2)[0]
            elif op == 0x29:
                d = struct.unpack_from('<i', ins, (pc+1)*2)[0]
            elif op <= 0x37:
                d = struct.unpack_from('<h', ins, (pc+1)*2)[0]
            else:
                d = struct.unpack_from('<b', ins, pc*2+1)[0]
            extra = f'-> {pc + 1 + d}'
        print(f'  {pc:04d} {name} {extra}')
        pc += size
    break
