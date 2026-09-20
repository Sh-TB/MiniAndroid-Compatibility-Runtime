#!/usr/bin/env python3
"""s72_w4_disasm2.py <apk> <Lclass;> — list methods + disassemble run/loop bodies."""
import sys, zipfile, struct, io

def uleb(f):
    r = 0; s = 0
    while True:
        b = f.read(1)[0]; r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r

apk, cls = sys.argv[1], sys.argv[2]
want = sys.argv[3] if len(sys.argv) > 3 else None
z = zipfile.ZipFile(apk)
d = z.read([n for n in z.namelist() if n.endswith('.dex')][0])
ssz, sof = struct.unpack_from('<II', d, 0x38)
tsz, tof = struct.unpack_from('<II', d, 0x40)
msz, mof = struct.unpack_from('<II', d, 0x58)
cdsz, cdof = struct.unpack_from('<II', d, 0x60)

def string(idx):
    off = struct.unpack_from('<I', d, sof + idx*4)[0]
    f = io.BytesIO(d); f.seek(off); n = uleb(f)
    return f.read(n).decode('utf-8', 'replace')

def tdesc(idx):
    return string(struct.unpack_from('<I', d, tof + idx*4)[0])

def method_sig(midx):
    ci, pi, ni = struct.unpack_from('<HHI', d, mof + midx*8)
    ro = struct.unpack_from('<I', d, tof + pi*12 + 4)[0]
    po = struct.unpack_from('<I', d, tof + pi*12 + 8)[0]
    params = ""
    if po:
        psz, = struct.unpack_from('<I', d, po)
        for k in range(psz):
            pti = struct.unpack_from('<I', d, po + 4 + k*4)[0]
            params += tdesc(pti)
    return f"{tdesc(ci)}->{string(ni)}({params}){tdesc(ro)}"

NAMES = {0x00:'nop',0x01:'move',0x0b:'return-void',0x0c:'return',0x0d:'return-wide',
0x0e:'return-object',0x0f:'const/4',0x10:'const/16',0x13:'const',0x16:'const-wide/16',
0x1a:'const-string',0x1c:'const-class',0x1f:'check-cast',0x21:'instance-of',
0x22:'new-instance',0x23:'new-array',0x27:'throw',0x28:'goto',0x29:'goto/16',
0x33:'if-eq',0x34:'if-ne',0x35:'if-lt',0x36:'if-ge',0x37:'if-gt',0x38:'if-le',
0x39:'if-eqz',0x3a:'if-nez',0x3b:'if-ltz',0x3c:'if-gez',0x3d:'if-gtz',0x3e:'if-lez',
0x44:'aget',0x46:'aget-object',0x4b:'aput',0x4d:'aget-wide',0x4f:'iget',0x52:'iget-object',
0x54:'iget-boolean',0x55:'iget-wide',0x59:'iput',0x5b:'iput-object',0x5e:'iput-wide',
0x5f:'sget',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-wide',0x67:'sput',
0x69:'sput-object',0x6b:'sput-wide',0x6e:'invoke-virtual',0x6f:'invoke-super',
0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
0x74:'invoke-virtual/range',0x77:'invoke-static/range',0x7b:'int-to-long',
0x7f:'int-to-float',0x81:'long-to-float',0x84:'int-to-float',0x8f:'long-to-float',
0x90:'float-to-int',0x91:'float-to-long',0xa0:'add-int',0xa3:'sub-int',
0xab:'add-int/2addr',0xad:'sub-int/2addr',0xaf:'mul-int/2addr',0xb0:'div-int/2addr',
0xbb:'add-float/2addr',0xbd:'sub-float/2addr',0xbf:'mul-float/2addr',
0xc0:'div-float/2addr',0xca:'add-long/2addr',0xd8:'add-int/lit8',0xda:'sub-int/lit8',
0xdb:'mul-int/lit8',0xdc:'div-int/lit8',0xdd:'rem-int/lit8',0xdf:'shl-int/lit8'}

for i in range(cdsz):
    base = cdof + i*32
    ci = struct.unpack_from('<I', d, base)[0]
    if tdesc(ci) != cls: continue
    cdo = struct.unpack_from('<I', d, base+24)[0]
    f = io.BytesIO(d); f.seek(cdo)
    ss = uleb(f); ins = uleb(f); dm = uleb(f); acc = 0
    for _ in range(ss):          # static fields: (diff, flags) pairs
        uleb(f); uleb(f)
    for _ in range(ins):         # instance fields
        uleb(f); uleb(f)
    methods = []
    for _ in range(dm):
        diff = uleb(f); ac = uleb(f); co = uleb(f); acc += diff
        methods.append((acc, co))
    vm = uleb(f); acc = 0
    for _ in range(vm):
        diff = uleb(f); ac = uleb(f); co = uleb(f); acc += diff
        methods.append((acc, co))
    for midx, co in methods:
        sig = method_sig(midx)
        name = sig.split('->')[1].split('(')[0]
        if want and name != want: continue
        print(f"== {sig}  code_off={hex(co)}")
        if co == 0: continue
        insns_size, = struct.unpack_from('<I', d, co+12)
        insns_of = co + 16
        units = struct.unpack_from('<%dH' % insns_size, d, insns_of)
        pc = 0
        while pc < insns_size:
            op = units[pc] & 0xff
            nm = NAMES.get(op, 'op-%02x' % op)
            line = f"  {pc:4d}: {nm}"
            if op in (0x6e,0x6f,0x70,0x71,0x72) and pc+2 < insns_size:
                line += f" {method_sig(units[pc+1])}"
                pc += 3
            elif op == 0x1a and pc+1 < insns_size:
                line += f" \"{string(units[pc+1])[:44]}\""
                pc += 2
            elif op in (0x39,0x3a,0x3b,0x3c,0x3d,0x3e):
                tgt = struct.unpack_from('<h', d, insns_of + (pc+1)*2)[0]
                line += f" v{units[pc]&0xf} -> {pc*2 + tgt*2}"
                pc += 2
            elif op in (0x28,):
                tgt = struct.unpack_from('<b', d, insns_of + pc*2 + 1)[0]
                line += f" -> {pc*2 + tgt*2}"
                pc += 1
            else:
                pc += 1
            print(line)
    break
