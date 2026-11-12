#!/usr/bin/env python3
"""S222-A step 2: dump Lnt1; (MultiParagraphLayoutCache) — fields, methods,
and disassembly of the density-touching methods. Also Lsg0;.b(J) packing law."""
import struct, zipfile, sys

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80):
            break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
proto_size, proto_off = struct.unpack_from("<2I", dex, 0x48)
f_size, f_off = struct.unpack_from("<2I", dex, 0x50)
m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)

def str_at(si):
    if si >= str_size: return f"str@{si}??"
    off = str_off_arr[si]
    _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode("utf-8", "replace")

tds = [str_at(struct.unpack_from("<I", dex, type_off + t*4)[0]) for t in range(type_size)]
protos = [struct.unpack_from("<3I", dex, proto_off + i*12) for i in range(proto_size)]
mids = [struct.unpack_from("<HHI", dex, m_off + i*8) for i in range(m_size)]
fids = [struct.unpack_from("<HHI", dex, f_off + i*8) for i in range(f_size)]

def proto_str(pi):
    if pi >= proto_size: return "??"
    _, ret, po = protos[pi]
    ps = ""
    if po:
        n = struct.unpack_from("<I", dex, po)[0]
        ps = "".join(tds[struct.unpack_from("<H", dex, po+4+k*2)[0]] for k in range(n))
    return f"({ps}){tds[ret]}"

SZT = [1]*256
for op in range(0x04,0x08): SZT[op]=2
SZT[0x13]=2; SZT[0x14]=3; SZT[0x16]=2; SZT[0x17]=3; SZT[0x18]=5; SZT[0x19]=2
SZT[0x1a]=2; SZT[0x1b]=3
SZT[0x1c]=2; SZT[0x1f]=2; SZT[0x20]=2
SZT[0x24]=3; SZT[0x25]=3; SZT[0x26]=3
SZT[0x29]=2; SZT[0x2a]=3; SZT[0x2b]=3; SZT[0x2c]=3
for op in range(0x2d,0x32): SZT[op]=2
for op in range(0x32,0x3e): SZT[op]=2
for op in range(0x44,0x52): SZT[op]=2
for op in range(0x52,0x60): SZT[op]=2
for op in range(0x60,0x6e): SZT[op]=2
for op in range(0x6e,0x73): SZT[op]=3
for op in range(0x74,0x79): SZT[op]=3
for op in range(0x90,0xb0): SZT[op]=2
for op in range(0xd0,0xe3): SZT[op]=2
SZT[0xe3]=1; SZT[0xe4]=1
for op in range(0xe5,0xea): SZT[op]=2
SZT[0xea]=2; SZT[0xeb]=2; SZT[0xec]=2; SZT[0xed]=2; SZT[0xee]=2; SZT[0xef]=2
SZT[0xf0]=2; SZT[0xf1]=2
SZT[0xfa]=3; SZT[0xfb]=3; SZT[0xfc]=3; SZT[0xfd]=3
SZT[0xfe]=2; SZT[0xff]=2

NAMES = {0x00:'nop',0x01:'move',0x02:'move/from16',0x03:'move/16',0x04:'move-wide',0x05:'move-wide/from16',
0x06:'move-wide/16',0x07:'move-object',0x08:'move-object/from16',0x09:'move-object/16',0x0a:'move-result',
0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',0x0e:'return-void',0x0f:'return',
0x10:'return-wide',0x11:'return-object',0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',
0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',0x19:'const-wide/high16',0x1a:'const-string',
0x1b:'const-string/jumbo',0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',0x1f:'check-cast',
0x20:'instance-of',0x21:'array-length',0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',
0x25:'filled-new-array/range',0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',
0x2b:'packed-switch',0x2c:'sparse-switch',0x2d:'cmpl-float',0x2e:'cmpg-float',0x2f:'cmpl-double',
0x30:'cmpg-double',0x31:'cmp-long',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',
0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez',
0x3e:'unused-3e',0x3f:'unused-3f',0x40:'unused-40',0x41:'unused-41',0x42:'unused-42',0x43:'unused-43'}
AGET = {0x44:'aget',0x45:'aget-wide',0x46:'aget-object',0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',
0x4a:'aget-short',0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',0x4f:'aput-byte',
0x50:'aput-char',0x51:'aput-short'}
IGET = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',0x57:'iget-char',
0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',
0x5e:'iput-char',0x5f:'iput-short'}
SGET = {0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',
0x66:'sget-short',0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',
0x6c:'sput-char',0x6d:'sput-short'}
INV = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',0x71:'invoke-static',
0x72:'invoke-interface',0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
0x77:'invoke-static/range',0x78:'invoke-interface/range'}
BIN2 = {0x90:'add-int',0x91:'sub-int',0x92:'mul-int',0x93:'div-int',0x94:'rem-int',0x95:'and-int',
0x96:'or-int',0x97:'xor-int',0x98:'shl-int',0x99:'shr-int',0x9a:'ushr-int',0x9b:'add-long',
0x9c:'sub-long',0x9d:'mul-long',0x9e:'div-long',0x9f:'rem-long',0xa0:'and-long',0xa1:'or-long',
0xa2:'xor-long',0xa3:'shl-long',0xa4:'shr-long',0xa5:'ushr-long',0xa6:'add-float',0xa7:'sub-float',
0xa8:'mul-float',0xa9:'div-float',0xaa:'rem-float',0xab:'add-double',0xac:'sub-double',0xad:'mul-double',
0xae:'div-double',0xaf:'rem-double'}

def opname(op):
    if op in NAMES: return NAMES[op]
    if op in AGET: return AGET[op]
    if op in IGET: return IGET[op]
    if op in SGET: return SGET[op]
    if op in INV: return INV[op]
    if op in BIN2: return BIN2[op]
    if 0x7b <= op <= 0x8f:
        un = {0x7b:'neg-int',0x7c:'not-int',0x7d:'neg-long',0x7e:'not-long',0x7f:'neg-float',
              0x80:'neg-double',0x81:'int-to-long',0x82:'int-to-float',0x83:'int-to-double',
              0x84:'long-to-int',0x85:'long-to-float',0x86:'long-to-double',0x87:'float-to-int',
              0x88:'float-to-long',0x89:'float-to-double',0x8a:'double-to-int',0x8b:'double-to-long',
              0x8c:'double-to-float',0x8d:'int-to-byte',0x8e:'int-to-char',0x8f:'int-to-short'}
        return un.get(op, f'unop-{op:#x}')
    if 0xb0 <= op <= 0xcf:
        two = ['add','sub','mul','div','rem','and','or','xor','shl','shr','ushr']
        k = (op - 0xb0) // 12; t = ['int','long','float','double'][k]
        return two[(op-0xb0)%12] + '-' + t + '/2addr'
    if 0xd0 <= op <= 0xd7:
        k = (op - 0xd0) // 4; t = ['int','long'][k]
        two = ['add','sub','mul','div','rem','and','or','xor','shl','shr','ushr']
        return two[(op-0xd0)%4] + '-' + t + '/lit16'
    if 0xd8 <= op <= 0xe2:
        two = ['add','sub','mul','div','rem','and','or','xor','shl','shr','ushr']
        return two[(op-0xd8)%11] + '-int/lit8'
    return f'op-{op:#x}'

def field_str(fidx):
    if fidx >= f_size: return f"field@{fidx}??"
    fc, ft, fn = fids[fidx]
    return f"{tds[fc]}.{str_at(fn)}:{tds[ft]}"

def meth_str(mi):
    if mi >= m_size: return f"meth@{mi}??"
    mc, mp, mn = mids[mi]
    return f"{tds[mc]}->{str_at(mn)}{proto_str(mp)}"

def disasm(co, maxn=10000):
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from("<4H2I", dex, co)
    base = co + 16
    out = []
    j = 0
    end = insns_size*2
    while j < end and len(out) < maxn:
        u = j // 2
        op = dex[base + j]
        sz = SZT[op]
        raw = dex[base+j:base+j+sz*2]
        line = f"  @{u:04x}: {opname(op)}"
        if op in (0x1a,):
            sidx = struct.unpack_from("<H", raw, 2)[0]
            line += f" v{raw[1]&0xf}, str@{sidx}({str_at(sidx)[:40]!r})"
        elif op in (0x1b,):
            sidx = struct.unpack_from("<I", raw, 2)[0]
            line += f" v{raw[1]&0xf}, str@{sidx}({str_at(sidx)[:40]!r})"
        elif 0x52 <= op <= 0x5f or 0x60 <= op <= 0x6d:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            fidx = struct.unpack_from("<H", raw, 2)[0]
            if op <= 0x58:
                line += f" v{raw[1]&0xf}, v{(raw[1]>>4)&0xf}, {field_str(fidx)}"
            else:
                line += f" v{(raw[1]>>4)&0xf}, {field_str(fidx)}"
        elif op in (0x6e,0x6f,0x70,0x71,0x72):
            if len(raw) < 6: out.append(line + " <trunc>"); j += sz*2; continue
            midx = struct.unpack_from("<H", raw, 2)[0]
            nregs = raw[1] >> 4
            regs_l = []
            for i in range(min(nregs, 5)):
                bi = 2 + i//2
                if bi < len(raw):
                    regs_l.append(str((raw[bi] >> 4) & 0xF if i % 2 else raw[bi] & 0xF))
                else:
                    regs_l.append('?')
            line += f" {{{','.join(regs_l)}}}, {meth_str(midx)}"
        elif op in (0x74,0x75,0x76,0x77,0x78):
            if len(raw) < 6: out.append(line + " <trunc>"); j += sz*2; continue
            midx = struct.unpack_from("<H", raw, 2)[0]
            line += f" v{raw[1]}, n={raw[2]&0xff}, {meth_str(midx)}"
        elif op == 0x22 or op == 0x20 or op == 0x1f or op == 0x1c:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            tidx = struct.unpack_from("<H", raw, 2)[0]
            line += f" {tds[tidx] if tidx < type_size else tidx}"
        elif op == 0x12:
            line += f" v{raw[1]&0xf}, {(raw[1]>>4)&0xf}"
        elif op == 0x13 or op == 0x16:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            v = struct.unpack_from("<h", raw, 2)[0]
            line += f" v{raw[1]}, {v}"
        elif op == 0x14 or op == 0x17:
            if len(raw) < 6: out.append(line + " <trunc>"); j += sz*2; continue
            v = struct.unpack_from("<i", raw, 2)[0]
            line += f" v{raw[1]}, {v:#x}" if op==0x14 else f" v{raw[1]}, {v}"
        elif op == 0x15 or op == 0x19:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            v = struct.unpack_from("<H", raw, 2)[0]
            line += f" v{raw[1]}, 0x{v<<16:x}"
        elif op == 0x18:
            if len(raw) < 10: out.append(line + " <trunc>"); j += sz*2; continue
            v = struct.unpack_from("<q", raw, 2)[0]
            line += f" v{raw[1]&0xf}, {v:#x}"
        elif op == 0x28:
            off = struct.unpack_from("<b", raw, 1)[0]
            line += f" -> {u + off:#x}"
        elif op == 0x29:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            off = struct.unpack_from("<h", raw, 2)[0]
            line += f" v{raw[1]} -> {u + off:#x}"
        elif op == 0x2a:
            if len(raw) < 6: out.append(line + " <trunc>"); j += sz*2; continue
            off = struct.unpack_from("<i", raw, 2)[0]
            line += f" -> {u + off:#x}"
        elif 0x32 <= op <= 0x37:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            off = struct.unpack_from("<h", raw, 2)[0]
            line += f" v{raw[1]&0xf}, v{(raw[1]>>4)&0xf} -> {u+off:#x}"
        elif 0x38 <= op <= 0x3d:
            if len(raw) < 4: out.append(line + " <trunc>"); j += sz*2; continue
            off = struct.unpack_from("<h", raw, 2)[0]
            line += f" v{raw[1]} -> {u+off:#x}"
        elif 0x44 <= op <= 0x51:
            line += f" v{raw[1]&0xf}, v{(raw[1]>>4)&0xf}, v{raw[2]&0xf}"
        elif op == 0x21:
            line += f" v{raw[1]&0xf}, v{(raw[1]>>4)&0xf}"
        out.append(line)
        j += sz*2
    return out

def class_by_desc(desc):
    for i in range(c_size):
        cls = struct.unpack_from("<IIIIIIII", dex, c_off + i*32)
        ci, sd_off = cls[0], cls[6]
        if sd_off == 0: continue
        if tds[ci] != desc: continue
        return cls, sd_off
    return None, 0

def dump_class(desc, want_methods=None, full=False):
    cls, o = class_by_desc(desc)
    if not cls:
        print("class not found", desc); return
    ci, acc, sup, ifc, _, _, sd, sv = cls
    print(f"CLASS {desc} acc={acc:#x} super={tds[sup] if sup < type_size else sup}")
    sf, o2 = uleb(dex, o); inf, o2 = uleb(dex, o2); dm, o2 = uleb(dex, o2); vm, o2 = uleb(dex, o2)
    fi = 0
    for _ in range(sf):
        d, o2 = uleb(dex, o2); fi += d
        accf, o2 = uleb(dex, o2)
        fc, ft, fn = fids[fi]
        print(f"  STATIC-FIELD {str_at(fn)}:{tds[ft]} acc={accf:#x}")
    fi = 0
    for _ in range(inf):
        d, o2 = uleb(dex, o2); fi += d
        accf, o2 = uleb(dex, o2)
        fc, ft, fn = fids[fi]
        print(f"  FIELD {str_at(fn)}:{tds[ft]} acc={accf:#x}")
    mi = 0
    for _ in range(dm):
        d, o2 = uleb(dex, o2); mi += d
        accm, o2 = uleb(dex, o2); co, o2 = uleb(dex, o2)
        mc, mp, mn = mids[mi]
        sig = f"{desc}->{str_at(mn)}{proto_str(mp)}"
        if co:
            regs, insz, outs, tries, dbg, insns_size = struct.unpack_from("<4H2I", dex, co)
            print(f"  DIRECT {str_at(mn)}{proto_str(mp)} acc={accm:#x} code@{hex(co)} regs={regs} ins={insz}")
            if full or (want_methods and (str_at(mn), proto_str(mp)) in want_methods):
                for l in disasm(co): print(l)
        else:
            print(f"  DIRECT {str_at(mn)}{proto_str(mp)} acc={accm:#x} (abstract/native)")
    for _ in range(vm):
        d, o2 = uleb(dex, o2); mi += d
        accm, o2 = uleb(dex, o2); co, o2 = uleb(dex, o2)
        mc, mp, mn = mids[mi]
        sig = (str_at(mn), proto_str(mp))
        if co:
            regs, insz, outs, tries, dbg, insns_size = struct.unpack_from("<4H2I", dex, co)
            print(f"  VIRTUAL {str_at(mn)}{proto_str(mp)} acc={accm:#x} code@{hex(co)} regs={regs} ins={insz}")
            if full or (want_methods and sig in want_methods):
                for l in disasm(co): print(l)
        else:
            print(f"  VIRTUAL {str_at(mn)}{proto_str(mp)} acc={accm:#x} (abstract/native)")

if __name__ == "__main__":
    import io, contextlib
    args = sys.argv[1:]
    if not args:
        print("usage: s222_dump_nt1.py <class-desc> [method-name ...] [--full]")
        sys.exit(1)
    desc = args[0]
    full = "--full" in args
    want = [(a, None) for a in args[1:] if not a.startswith("--")]
    if want:
        # dump any method whose NAME matches (any proto)
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dump_class(desc, full=True)
        for line in buf.getvalue().splitlines():
            if line.startswith("  ") and ("->" in line):
                mname = line.split("->")[1].split("(")[0] if "->" in line else ""
            else:
                continue
            if line.startswith(("  DIRECT", "  VIRTUAL")):
                codepart = line.split("code@")[0]
                meth = line.split("  ")[1].split(" acc=")[0]
                nm = meth.split("(")[0]
                if full or nm in [w[0] for w in want]:
                    print(line)
                    # extract code@ offset and re-disasm
                    if "code@" in line:
                        co = int(line.split("code@")[1].split(" ")[0], 16)
                        for l in disasm(co): print(l)
                else:
                    print(line)
    else:
        dump_class(desc, full=full)
