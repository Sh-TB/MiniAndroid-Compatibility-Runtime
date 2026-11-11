#!/usr/bin/env python3
"""S216 CONT-131 decode v4 — disassemble dooz methods with a full opcode-size
table; dumps invoke/const/branch views for the resume chain."""
import struct, zipfile

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
WANT = {("Lbt1;", "d"), ("Liw0;", "g"), ("Liw0;", "c"), ("Lbo;", "j"),
        ("Lsj;", "J"), ("Lor1;", "M0"), ("Lor1;", "L"), ("Lwt0;", "z0")}

z = zipfile.ZipFile(APK)

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

# dalvik opcode sizes in 16-bit code units (standard table)
SZ = [1]*256
for op in range(0x00,0x04): SZ[op]=1          # nop, move family small
for op in range(0x04,0x08): SZ[op]=2          # move/from16
SZ[0x07]=1; SZ[0x08]=1; SZ[0x09]=1
for op in range(0x0a,0x10): SZ[op]=1          # move-*, return-*
for op in range(0x10,0x13): SZ[op]=1          # const/4, const/4 wait
SZ[0x12]=1; SZ[0x13]=2; SZ[0x14]=3; SZ[0x15]=1; SZ[0x16]=2
SZ[0x17]=3; SZ[0x18]=5; SZ[0x19]=2
SZ[0x1a]=2; SZ[0x1b]=3                        # const-string, jumbo
SZ[0x1c]=2; SZ[0x1d]=1; SZ[0x1e]=1; SZ[0x1f]=2; SZ[0x20]=2
for op in range(0x21,0x24): SZ[op]=1
SZ[0x24]=3; SZ[0x25]=3; SZ[0x26]=3
SZ[0x27]=1
SZ[0x28]=1; SZ[0x29]=2; SZ[0x2a]=3
SZ[0x2b]=3; SZ[0x2c]=3
for op in range(0x2d,0x32): SZ[op]=2          # cmp kinds
for op in range(0x32,0x3e): SZ[op]=2          # if-*
for op in range(0x3e,0x44): SZ[op]=1          # unused/ nop-ish
for op in range(0x44,0x52): SZ[op]=2          # aget/aput
for op in range(0x52,0x60): SZ[op]=2          # iget/iput
for op in range(0x60,0x6e): SZ[op]=2          # sget/sput
for op in range(0x6e,0x73): SZ[op]=3          # invoke 35c
SZ[0x73]=1
for op in range(0x74,0x79): SZ[op]=3          # invoke range
for op in range(0x79,0x7b): SZ[op]=1
for op in range(0x7b,0x90): SZ[op]=1          # unop
for op in range(0x90,0xb0): SZ[op]=2          # binop
for op in range(0xb0,0xd0): SZ[op]=1          # binop/2addr
for op in range(0xd0,0xe3): SZ[op]=2          # binop/lit16
SZ[0xe3]=1; SZ[0xe4]=1
for op in range(0xe5,0xea): SZ[op]=2          # binop/lit8... actually 0xd4-0xe2
# 0xea-0xfb misc (some 2-3 units); payloads handled specially
SZ[0xeb]=2; SZ[0xec]=2; SZ[0xed]=2; SZ[0xee]=2; SZ[0xef]=2
SZ[0xf0]=2; SZ[0xf1]=2
SZ[0xfa]=3; SZ[0xfb]=3  # invoke-polymorphic
SZ[0xfc]=3; SZ[0xfd]=3  # invoke-custom
SZ[0xfe]=2; SZ[0xff]=2

INVOKE = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
          0x71:'invoke-static',0x72:'invoke-interface',
          0x74:'invoke-virtual/range',0x76:'invoke-direct/range',
          0x77:'invoke-static/range',0x78:'invoke-interface/range'}
BR = {0x28:'goto',0x29:'goto/16',0x2a:'goto/32',0x2b:'packed-switch',
      0x2c:'sparse-switch',0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',
      0x35:'if-ge',0x36:'if-gt',0x37:'if-le',0x38:'if-eqz',0x39:'if-nez',
      0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}

for dn in [n for n in z.namelist() if n.endswith('.dex')]:
    dex = z.read(dn)
    str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
    type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
    p_size, p_off = struct.unpack_from("<2I", dex, 0x48)
    m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
    c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
    str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)
    def str_at(si):
        off = str_off_arr[si]
        _, o = uleb(dex, off)
        return dex[o:dex.index(b"\x00", o)].decode("utf-8", "replace")
    tds = [str_at(struct.unpack_from("<I", dex, type_off + t*4)[0]) for t in range(type_size)]
    def proto_s(pi):
        sidx, ridx, poff = struct.unpack_from("<III", dex, p_off + pi*12)
        params = []
        if poff:
            n = struct.unpack_from("<I", dex, poff)[0]
            for k in range(n):
                ti = struct.unpack_from("<H", dex, poff + 4 + k*2)[0]
                params.append(tds[ti])
        return f"({','.join(params)}){tds[ridx]}"
    def mid(idx):
        ci, pi, ni = struct.unpack_from("<HHI", dex, m_off + idx*8)
        return tds[ci], proto_s(pi), str_at(ni)
    def disasm(code_off):
        ins_off = struct.unpack_from("<I", dex, code_off + 12)[0]
        ins_n = struct.unpack_from("<I", dex, code_off + 8)[0] >> 16
        end = ins_off + ins_n*2
        out, u = [], ins_off
        while u + 1 < end:
            w = struct.unpack_from("<H", dex, u)[0]
            op = w & 0xFF
            pc = (u - ins_off)//2
            if op in INVOKE:
                midx = struct.unpack_from("<H", dex, u+2)[0]
                cc, desc, nm = mid(midx)
                out.append(f"@{pc:04x} {INVOKE[op]} {cc}.{nm}{desc}")
            elif op == 0x1a:
                si = struct.unpack_from("<H", dex, u+2)[0]
                out.append(f'@{pc:04x} const-string "{str_at(si)[:60]}"')
            elif op == 0x1b:
                si = struct.unpack_from("<I", dex, u+2)[0]
                out.append(f'@{pc:04x} const-string/jumbo "{str_at(si)[:60]}"')
            elif op in BR:
                if op == 0x28:
                    tgt = struct.unpack_from("<b", dex, u+1)[0]
                elif op == 0x29:
                    tgt = struct.unpack_from("<h", dex, u+2)[0]
                else:
                    tgt = struct.unpack_from("<i", dex, u+2)[0]
                out.append(f"@{pc:04x} {BR[op]} -> {pc+tgt:+d}")
            elif op == 0x12:
                out.append(f"@{pc:04x} const/4 v?, #{w>>12 & 0xF: d}" if False else f"@{pc:04x} const/4")
            elif op == 0x00 and w == 0x0000:
                pass
            u += SZ[op]*2
        return out
    found = 0
    for c in range(c_size):
        cd = struct.unpack_from("<8I", dex, c_off + c*32)
        if tds[cd[0]] not in {w[0] for w in WANT}: continue
        try:
            o = cd[6]
            sfs, o = uleb(dex, o); ifs, o = uleb(dex, o)
            dms, o = uleb(dex, o); vms, o = uleb(dex, o)
            for _ in range(sfs + ifs):
                _, o = uleb(dex, o); _, o = uleb(dex, o)
            midx = 0
            for i in range(dms + vms):
                diff, o = uleb(dex, o); acc, o = uleb(dex, o); code, o = uleb(dex, o)
                midx += diff
                try:
                    cc, desc, nm = mid(midx)
                except Exception:
                    break
                if (cc, nm) not in WANT: continue
                found += 1
                print(f"==== {cc}.{nm}{desc} code=0x{code:x}")
                for line in disasm(code):
                    print("  " + line)
        except Exception as e:
            print(f"  (walk failed: {e})")
    if found:
        print(f"({dn}: {found} methods)")
