#!/usr/bin/env python3
"""F-028e: complete AOSP opcode-size table walk. Finds the offset that makes
b2/n.d's instruction stream self-consistent (valid opcodes, exact end)."""
import struct, zipfile, sys
sys.path.insert(0, '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tools')
import exp059_disasm as d

# Dalvik instruction size in code units per opcode (0x00-0xff).
SIZE = {}
def S(ops, n):
    for o in ops: SIZE[o] = n
S(range(0x00, 0x12), 1)          # nop..return-object (except /16 variants)
S([0x02,0x05,0x08], 2)           # move/from16, move-wide/from16, move-object/from16
S([0x03,0x06,0x09], 3)           # move/16 family
S(range(0x0a, 0x0d), 1)          # move-result family
S([0x12,0x13,0x15,0x16,0x17,0x19,0x1c,0x1d,0x1e,0x1f,0x20,0x21,0x22,0x23], 2)  # 21c/21s/21t/21h/22x/21t
S([0x14], 3)                     # const (31i)
S([0x18], 5)                     # const-wide (51l)
S([0x1a,0x1b], 2)                # const-string (+jumbo 3)
SIZE[0x1b] = 3
S([0x24,0x25], 3)                # filled-new-array (+range)
S([0x26], 3)                     # fill-array-data (31t)
S([0x27], 1)                     # throw
S([0x28], 1)                     # goto
S([0x29], 2)                     # goto/16
S([0x2a], 3)                     # goto/32
S([0x2b,0x2c], 3)                # packed/sparse-switch (31t)
S(range(0x2d, 0x32), 2)          # cmp family 23x
S(range(0x32, 0x38), 3)          # if-eq..if-le 22t
S(range(0x38, 0x3e), 2)          # if-eqz..if-lez 21t
S(range(0x44, 0x52), 2)          # aget/aput 23x
S(range(0x52, 0x60), 2)          # iget/iput 22c
S(range(0x60, 0x6d), 2)          # sget/sput 21c
S(range(0x6e, 0x73), 3)          # invokes 35c
S(range(0x74, 0x79), 3)          # invokes range 3rc
S(range(0x7b, 0x90), 1)          # unary 12x (neg/int-to-*)
S(range(0x90, 0xb0), 2)          # binop 23x
S(range(0xb0, 0xd0), 1)          # binop/2addr 12x
S(range(0xd0, 0xd8), 2)          # binop/lit16 22b
S(range(0xd8, 0xe0), 2)          # binop/lit8 22b
S(range(0xe0, 0xfa), 2)          # unused; d8 shouldn't emit — treat 2 to fail loudly
S([0xfa], 3)                     # iget-wide/jumbo?? unused
# everything else: unknown → mark
for o in range(0x100):
    SIZE.setdefault(o, None)

def main():
    with zipfile.ZipFile(d.APK) as z:
        data = z.read('classes.dex')
    dex = d.load_dex(data)
    insns_off, regs, ins, outs, tries, insns_size = d.find_method(dex, 'Lb2/n;', 'd')
    def cu(i): return struct.unpack_from('<H', data, insns_off + i*2)[0]
    for delta in (0, 1, -1, 2, -2):
        start_ok = True
        pc = delta
        steps = []
        while 0 <= pc < insns_size:
            op = cu(pc) & 0xff
            sz = SIZE[op]
            if sz is None:
                start_ok = False
                steps.append((pc, op, 'BAD'))
                break
            steps.append((pc, op, sz))
            pc += sz
        ok = start_ok and pc == insns_size
        print(f'offset={delta:+d}: walked_to={pc} insns_size={insns_size} consistent={ok}')
        if not ok and delta == 0:
            print('  first-bad tail:', steps[-4:])

if __name__ == '__main__':
    main()
