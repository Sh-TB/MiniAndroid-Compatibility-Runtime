#!/usr/bin/env python3
"""CONT-136: disassemble a named method from dooz classes.dex (raw opcodes + refs).
Usage: cont136_disasm.py <class-desc like Lt4;> <method-name> [max-insns]
"""
import struct, zipfile, sys

APK = 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from('<2I', dex, 0x38)
type_size, type_off = struct.unpack_from('<2I', dex, 0x40)
f_size, f_off = struct.unpack_from('<2I', dex, 0x50)
m_size, m_off = struct.unpack_from('<2I', dex, 0x58)
c_size, c_off = struct.unpack_from('<2I', dex, 0x60)
soa = struct.unpack_from(f'<{str_size}I', dex, str_off)

def str_at(si):
    off = soa[si]; _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode('utf-8', 'replace')

tds = [str_at(struct.unpack_from('<I', dex, type_off + t * 4)[0]) for t in range(type_size)]
fids = []
for i in range(f_size):
    ci, ti, ni = struct.unpack_from('<HHI', dex, f_off + i * 8)
    fids.append((tds[ci], tds[ti], str_at(ni)))
mids = []
for i in range(m_size):
    ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + i * 8)
    mids.append((tds[ci], str_at(ni)))  # skip proto for brevity

CLS = sys.argv[1] if len(sys.argv) > 1 else 'Lt4;'
MNAME = sys.argv[2] if len(sys.argv) > 2 else 'onDraw'
MAXI = int(sys.argv[3]) if len(sys.argv) > 3 else 400

OPS = {
0x00:'nop',0x01:'move',0x04:'move-wide',0x07:'move-object',0x0a:'move-result',0x0b:'move-result-wide',
0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',0x0f:'return',0x10:'return-wide',
0x11:'return-object',0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',0x16:'const-wide/16',
0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',0x1c:'const-class',0x1d:'monitor-enter',
0x1e:'monitor-exit',0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',
0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',0x26:'fill-array-data',
0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch',
0x2d:'cmpl-float',0x2f:'cmpg-float',0x31:'cmpl-double',0x33:'cmpg-double',0x34:'cmp-long',
0x35:'if-eq',0x36:'if-ne',0x37:'if-lt',0x38:'if-ge',0x39:'if-gt',0x3a:'if-le',
0x3b:'if-eqz',0x3c:'if-nez',0x3d:'if-ltz',0x3e:'if-gez',0x3f:'if-gtz',0x40:'if-lez',
0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',
0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',
0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x68:'sput',0x69:'sput-wide',0x6a:'sput-object',
0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
0x74:'invoke-virtual/range',0x76:'invoke-direct/range',0x77:'invoke-static/range',0x78:'invoke-interface/range',
0x7b:'int-to-long',0x81:'long-to-int',0x84:'int-to-float',0x85:'int-to-double',0x88:'float-to-int',
0x8b:'double-to-int',0x8f:'float-to-double',0x90:'double-to-float',0x91:'int-to-byte',
0x94:'add-int',0x9b:'add-long',0xa0:'add-float',0xa3:'sub-int',0xa8:'sub-float',0xab:'mul-int',
0xb0:'mul-float',0xbb:'div-long',0xbd:'rem-long',0xbf:'rem-float',0xc0:'rem-double',0xd0:'add-int/lit16',
0xd2:'mul-int/lit16',0xd5:'sub-int/lit16',0xd8:'add-int/lit8',0xda:'mul-int/lit8',0xdb:'div-int/lit8',
0xdd:'rem-int/lit8',0xde:'and-int/lit8',0xe0:'xor-int/lit8',0xdf:'or-int/lit8',
}

for c in range(c_size):
    cd = struct.unpack_from('<8I', dex, c_off + c * 32)
    cls = tds[cd[0]]
    if cls != CLS: continue
    o = cd[6]
    if o == 0: continue
    sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
    fidx = 0
    for _ in range(sfs):
        d, o = uleb(dex, o); a, o = uleb(dex, o); fidx += d
    fidx = 0
    for _ in range(ifs):
        d, o = uleb(dex, o); a, o = uleb(dex, o); fidx += d
    midx = 0
    for lst, cnt in (('DM', dms), ('VM', vms)):
        midx = 0  # CONT-130 law: deltas reset per list
        for i in range(cnt):
            d, o = uleb(dex, o); a, o = uleb(dex, o); co, o = uleb(dex, o)
            midx += d
            if co == 0 or midx >= m_size: continue
            if mids[midx][1] != MNAME: continue
            print(f'== {cls};.{MNAME} ({lst}) code@{co}')
            regs, ins, outs, tries = struct.unpack_from('<4H', dex, co)
            dbg, insns = struct.unpack_from('<2I', dex, co + 8)
            body = dex[co + 16: co + 16 + insns * 2]
            print(f'   regs={regs} ins={ins} outs={outs} insns={insns}')
            pc = 0; shown = 0
            while pc < len(body) and shown < MAXI:
                op = body[pc]
                nm = OPS.get(op, f'op{op:#04x}')
                # instruction sizes in code units (approx: covers used set)
                sz = {0x00:1,0x12:1,0x0e:1,0x0f:1,0x10:1,0x11:1,0x27:1,0x1d:1,0x1e:1}.get(op)
                if sz is None:
                    if op in (0x13,0x15,0x16,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x28,0x69,0x6a,0x62,0x68,0x61,0x60,0x54,0x53,0x52,0x5b,0x5a,0x59,0x4c,0x4b,0x46,0x45,0x44,0x91,0x88,0x85,0x84,0x81,0x7b,0x21,0x0b,0x0a,0x0c,0x0d,0x01,0x04,0x07,0xd8,0xda,0xdb,0xdd,0xde,0xdf,0xe0): sz = 2
                    elif op in (0x14,0x17,0x18,0x19,0x29,0x2b,0x2c,0x26,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,0x40,0x6e,0x6f,0x70,0x71,0x72,0x24,0xd0,0xd2,0xd5,0x94,0x9b,0xa0,0xa3,0xa8,0xab,0xb0,0xbb,0xbd,0xbf,0xc0,0x34,0x31,0x33,0x2f,0x2d,0x8f,0x8b,0x90): sz = 3
                    elif op in (0x74,0x75,0x76,0x77,0x78,0x25,0x2a): sz = 4
                    else: sz = 1
                detail = ''
                if op == 0x1a:
                    si = struct.unpack_from('<H', body, pc + 2)[0]
                    detail = f' "{str_at(si)[:40]}"'
                elif op in (0x6e,0x6f,0x70,0x71,0x72):
                    mr = struct.unpack_from('<H', body, pc + 2)[0]
                    m = mids[mr] if mr < m_size else ('?','?')
                    detail = f' {m[0]};.{m[1]}'
                elif op in (0x74,0x76,0x77,0x78):
                    mr = struct.unpack_from('<H', body, pc + 4)[0]
                    m = mids[mr] if mr < m_size else ('?','?')
                    detail = f' {m[0]};.{m[1]}'
                elif op in (0x52,0x53,0x54,0x59,0x5a,0x5b,0x60,0x61,0x62,0x68,0x69,0x6a):
                    fr = struct.unpack_from('<H', body, pc + 2)[0]
                    f = fids[fr] if fr < f_size else ('?','?','?')
                    detail = f' {f[0]};.{f[2]}:{f[1]}'
                elif op == 0x22 or op == 0x1c or op == 0x20:
                    tr = struct.unpack_from('<H', body, pc + 2)[0]
                    detail = f' {tds[tr] if tr < type_size else "?"}'
                elif op in (0x12,):
                    detail = f' {body[pc+1] & 0xf:#x}'
                elif op in (0x28,):
                    off = body[pc+1] if body[pc+1] < 0x80 else body[pc+1] - 0x100
                    detail = f' -> {pc + off}'
                elif op in (0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,0x40) and sz == 3:
                    off = struct.unpack_from('<h', body, pc + 2)[0] if op >= 0x35 else 0
                    if op >= 0x3b:
                        off = struct.unpack_from('<h', body, pc + 2)[0]
                    detail = f' -> {pc + off}'
                print(f'   {pc:04d}: {nm}{detail}')
                pc += sz; shown += 1
