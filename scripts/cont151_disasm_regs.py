#!/usr/bin/env python3
"""cont151_disasm_regs.py — register-accurate Dalvik disassembler for one method.
Usage: cont151_disasm_regs.py <apk> <class-desc> <method-name> [max-insn-units]
Prints: idx: op operands  (regs resolved, field/method refs resolved)."""
import struct, zipfile, sys

APK = sys.argv[1]; CLS = sys.argv[2]; METH = sys.argv[3]
MAXI = int(sys.argv[4]) if len(sys.argv) > 4 else 400

z = zipfile.ZipFile(APK)
DEXES = sorted(n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

SIZES = [2]*256
for op in range(0x00, 0x08): SIZES[op] = 1   # nop/move-family 12x + returns
SIZES[0x0f]=1; SIZES[0x10]=1; SIZES[0x11]=1; SIZES[0x12]=1
SIZES[0x08]=2; SIZES[0x09]=2; SIZES[0x0a]=2; SIZES[0x0e]=2  # move/from16 22x
SIZES[0x0b]=1; SIZES[0x0c]=1; SIZES[0x0d]=1
SIZES[0x1d]=1; SIZES[0x1e]=1; SIZES[0x21]=1; SIZES[0x27]=1; SIZES[0x28]=1
for op in range(0x7b, 0x90): SIZES[op] = 1
for op in range(0xb0, 0xd0): SIZES[op] = 1
SIZES[0x13]=2; SIZES[0x15]=2; SIZES[0x16]=2; SIZES[0x19]=2
SIZES[0x14]=3; SIZES[0x18]=5
for op in range(0x38,0x3e): SIZES[op]=2   # 21t if-testz: op AA off16 = 2 units
SIZES[0x1a]=2; SIZES[0x1c]=2; SIZES[0x1f]=2; SIZES[0x20]=2
SIZES[0x22]=2; SIZES[0x23]=2
SIZES[0x17]=3; SIZES[0x1b]=3
SIZES[0x24]=3; SIZES[0x25]=3; SIZES[0x26]=3
SIZES[0x29]=2; SIZES[0x2a]=3; SIZES[0x2b]=3; SIZES[0x2c]=3
for op in range(0x2d,0x32): SIZES[op]=2
for op in range(0x44,0x52): SIZES[op]=2
for op in range(0x52,0x5e): SIZES[op]=2
SIZES[0x5e]=2; SIZES[0x5f]=2
for op in range(0x60,0x6e): SIZES[op]=2
for op in range(0x6e,0x73): SIZES[op]=3
for op in range(0x74,0x79): SIZES[op]=3
for op in range(0x90,0xb0): SIZES[op]=2
for op in range(0xd0,0xe3): SIZES[op]=2
SIZES[0xfa]=4; SIZES[0xfb]=4
SIZES[0xfc]=3; SIZES[0xfd]=3; SIZES[0xfe]=3; SIZES[0xff]=3

for DEXNAME in DEXES:
    dex = z.read(DEXNAME)
    str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
    type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
    proto_off = struct.unpack_from('<I', dex, 0x4C)[0]
    field_size, field_off = struct.unpack_from('<2I', dex, 0x50)
    meth_size, meth_off = struct.unpack_from('<2I', dex, 0x58)
    class_size, class_off = struct.unpack_from('<2I', dex, 0x60)
    soa = struct.unpack_from(f'<{str_size}I', dex, str_off)
    def str_at(si, _dex=dex, _soa=soa):
        off = _soa[si]; _, o = uleb(_dex, off)
        return _dex[o:_dex.index(b"\x00", o)].decode('utf-8', 'replace')
    tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
    fids = []
    for i in range(field_size):
        ci, ti, ni = struct.unpack_from('<HHI', dex, field_off + i * 8)
        fids.append((tds[ci], tds[ti], str_at(ni)))
    mids = []
    for i in range(meth_size):
        ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + i * 8)
        ret_idx = struct.unpack_from('<I', dex, proto_off + pi * 12 + 4)[0]
        mids.append((tds[ci], str_at(ni), tds[ret_idx] if ret_idx < type_size else '?'))

    def parse_methods(off, cnt, base=0):
        out = []; midx = base; p = off
        for _ in range(cnt):
            mdiff, p = uleb(dex, p)
            acc, p = uleb(dex, p)
            code_off, p = uleb(dex, p)
            midx += mdiff
            if code_off: out.append((midx, code_off, is_direct_flag if False else None))
        return out, p

    found = None
    for i in range(class_size):
        c = struct.unpack_from('<I', dex, class_off + i * 32)[0]
        if tds[c] != CLS: continue
        cdata = struct.unpack_from('<I', dex, class_off + i * 32 + 24)[0]
        if not cdata: continue
        p = cdata
        sf, p = uleb(dex, p); inf, p = uleb(dex, p)
        dm, p = uleb(dex, p); vm, p = uleb(dex, p)
        for _ in range(sf):
            _, p = uleb(dex, p); _, p = uleb(dex, p)
        for _ in range(inf):
            _, p = uleb(dex, p); _, p = uleb(dex, p)
        ml = []; midx = 0; p2 = p
        for _ in range(dm):
            mdiff, p2 = uleb(dex, p2); acc, p2 = uleb(dex, p2); code_off, p2 = uleb(dex, p2)
            midx += mdiff
            if code_off: ml.append((midx, code_off))
        midx = 0
        for _ in range(vm):
            mdiff, p2 = uleb(dex, p2); acc, p2 = uleb(dex, p2); code_off, p2 = uleb(dex, p2)
            midx += mdiff
            if code_off: ml.append((midx, code_off))
        for midx, code_off in ml:
            ci, pi, ni = struct.unpack_from('<HHI', dex, meth_off + midx * 8)
            if tds[ci] == CLS and str_at(ni) == METH:
                found = (code_off, f'insns={struct.unpack_from("<I", dex, code_off + 12)[0]}')
                break
        if found: break
    if not found: continue
    code_off, meta = found
    regs, ins, outs, tries, dbg, insz = struct.unpack_from('<4H2I', dex, code_off)
    print(f'== {CLS}.{METH} {meta} code@{code_off} regs={regs} ins={ins} outs={outs}')
    base = code_off + 16
    pc = 0
    def fref(i): return f'{fids[i][1]} {fids[i][2]}' if i < field_size else f'fld@{i}'
    def mref(i): return f'{mids[i][0]}.{mids[i][1]}' if i < meth_size else f'm@{i}'
    while pc < insz and pc < MAXI:
        u0, u1 = struct.unpack_from('<2H', dex, base + pc*2)
        unit = u0 | (u1 << 16) if False else u0
        if unit == 0x0100:
            n = struct.unpack_from('<H', dex, base + pc*2 + 2)[0]
            print(f'  {pc:4d}: packed-switch-payload size={n}'); pc += n*2 + 4; continue
        if unit == 0x0200:
            n = struct.unpack_from('<H', dex, base + pc*2 + 2)[0]
            print(f'  {pc:4d}: sparse-switch-payload size={n}'); pc += n*4 + 2; continue
        if unit == 0x0300:
            ew = struct.unpack_from('<H', dex, base + pc*2 + 2)[0]
            n = struct.unpack_from('<H', dex, base + pc*2 + 4)[0]
            print(f'  {pc:4d}: fill-array-data-payload ew={ew} n={n}')
            pc += (n*ew + 1)//2 + 4; continue
        op = unit & 0xff
        A = (u0 >> 8) & 0xf; B = (u0 >> 12) & 0xf
        AA = (u0 >> 8) & 0xff
        BBBB = struct.unpack_from('<H', dex, base + pc*2 + 2)[0] if SIZES[op] >= 2 else 0
        line = f'  {pc:4d}: '
        if op in (0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x0b,0x0c,0x0d):
            line += f'op{op:02x} v{A}, v{B}'
        elif op in (0x08,0x09,0x0a,0x0e):
            v16 = struct.unpack_from('<H', dex, base + pc*2 + 2)[0]
            line += f'op{op:02x} v{AA}, v{v16}'
        elif op in (0x0f,0x10,0x11):
            line += f'return v{AA}'
        elif op == 0x12:
            line += f'const/4 v{A}, #{B-16 if B>7 else B}'
        elif op == 0x00:
            line += 'nop'
        elif op < 0x13:   # 11x/22x fallback
            line += f'op{op:02x} v{AA}'
        elif op == 0x13 or op == 0x16 or op == 0x1a or op == 0x1c or op == 0x1f or op == 0x20 or op == 0x22 or op == 0x23 or 0x60 <= op <= 0x6d:
            if op in (0x1c,0x1f,0x20,0x22,0x23): line += f'op{op:02x} v{AA}, {tds[BBBB] if BBBB < type_size else BBBB}'
            elif op == 0x1a: line += f'const-string v{AA}, "{str_at(BBBB)}"'
            elif 0x60 <= op <= 0x6d: line += f'op{op:02x} v{AA}, {fref(BBBB)}'
            else: line += f'op{op:02x} v{AA}, #+{BBBB if BBBB < 0x8000 else BBBB-0x10000}'
        elif op in (0x14, 0x17):
            v = struct.unpack_from('<i', dex, base + pc*2 + 2)[0]
            line += f'op{op:02x} v{AA}, #{v}'
        elif op == 0x18:
            v = struct.unpack_from('<q', dex, base + pc*2 + 2)[0]
            line += f'const-wide v{AA}, #{v}'
        elif op == 0x15 or op == 0x19:
            line += f'op{op:02x} v{AA}, #+{BBBB<<16:#x}'
        elif op == 0x1b:
            v = struct.unpack_from('<I', dex, base + pc*2 + 2)[0]
            line += f'const-string/jumbo v{AA}, "{str_at(v)}"'
        elif 0x29 <= op <= 0x2c:
            if op == 0x29:
                t = pc + BBBB if BBBB < 0x8000 else pc + BBBB - 0x10000
                line += f'goto/16 +{BBBB} -> {t}'
            else:
                v = struct.unpack_from('<i', dex, base + pc*2 + 2)[0]
                line += f'op{op:02x} arg=#{v}'
        elif 0x2d <= op <= 0x31 or 0x44 <= op <= 0x51 or 0x90 <= op <= 0xaf:
            r2 = struct.unpack_from('<H', dex, base + pc*2 + 4)[0] if SIZES[op] >= 3 else 0
            if 0x90 <= op <= 0xaf:
                line += f'op{op:02x} v{A}, v{B}'
            else:
                line += f'op{op:02x} v{AA}, v{BBBB & 0xff}, v{(BBBB >> 8) & 0xff}'
        elif 0x32 <= op <= 0x37:  # 22t
            t = pc + BBBB if BBBB < 0x8000 else pc + BBBB - 0x10000
            line += f'op{op:02x} v{A}, v{B} -> {t}'
        elif 0x38 <= op <= 0x3d:  # 21t
            v = struct.unpack_from('<h', dex, base + pc*2 + 2)[0]
            line += f'op{op:02x} v{AA} -> {pc + v}'
        elif 0x52 <= op <= 0x5d:  # 22c
            line += f'op{op:02x} v{A}, v{B}, {fref(BBBB)}'
        elif 0x5e <= op <= 0x5f:  # 22b
            line += f'op{op:02x} v{AA}, v{BBBB & 0xff}, #{(BBBB >> 8) & 0xff}'
        elif 0xd0 <= op <= 0xd7:  # 22s
            line += f'op{op:02x} v{A}, v{B}, #{BBBB-0x10000 if BBBB>=0x8000 else BBBB}'
        elif 0xd8 <= op <= 0xe2:  # 22b
            line += f'op{op:02x} v{A}, v{B}, #{BBBB-0x10000 if BBBB>=0x8000 else BBBB}'
        elif 0x6e <= op <= 0x72:  # 35c
            cnt = (u0 >> 12) & 0xf; g = (u0 >> 8) & 0xf
            regs_l = struct.unpack_from('<H', dex, base + pc*2 + 4)[0]
            rl = [g, regs_l & 0xf, (regs_l >> 4) & 0xf, (regs_l >> 8) & 0xf, (regs_l >> 12) & 0xf][:cnt]
            line += f'invoke {mref(BBBB)} {{{", ".join("v"+str(r) for r in rl)}}}'
        elif 0x74 <= op <= 0x78:  # 3rc
            cnt = AA; start = struct.unpack_from('<H', dex, base + pc*2 + 4)[0]
            line += f'invoke-range {mref(BBBB)} {{v{start}..v{start+cnt-1}}}'
        elif op == 0x26:  # 31t fill-array-data
            v = struct.unpack_from('<i', dex, base + pc*2 + 2)[0]
            line += f'fill-array-data v{AA} -> payload@{pc + v}'
        elif op == 0x2b or op == 0x2c:  # 31t switch
            v = struct.unpack_from('<i', dex, base + pc*2 + 2)[0]
            line += f'{"packed" if op==0x2b else "sparse"}-switch v{AA} -> payload@{pc + v}'
        else:
            line += f'op{op:02x} raw={u1:#06x} ref={BBBB:#06x}'
        print(line)
        pc += SIZES[op]
    if pc >= MAXI: print(f'  ... (truncated at {MAXI} units of {insz})')
    sys.exit(0)
print(f'method {CLS}.{METH} NOT FOUND')
