#!/usr/bin/env python3
"""cont7w2_dex_xref.py — proper Dalvik decoder: const-string xref + method dump.
Sizes from the Dalvik bytecode instruction format table (all 256 opcodes).
Usage: cont7w2_dex_xref.py <apk|dex> <needle|idx=N> [class_filter] [--dump CLS METH]
"""
import sys, zipfile, struct

APK = sys.argv[1]
ARG2 = sys.argv[2]
CLSFILTER = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
DUMP = ('--dump' in sys.argv)
DUMPCLS = sys.argv[sys.argv.index('--dump')+1] if DUMP else None
DUMPMETH = sys.argv[sys.argv.index('--dump')+2] if DUMP and len(sys.argv) > sys.argv.index('--dump')+2 else None

if APK.endswith('.dex'):
    b = open(APK, 'rb').read()
else:
    z = zipfile.ZipFile(APK)
    b = z.read('classes.dex')

# ── instruction size table (16-bit code units), by opcode ──
S = [1]*256
S[0x00]=1  # nop (10x)
for o in range(0x01,0x0a): S[o]=1  # 12x
for o in range(0x0a,0x0e): S[o]=1  # 11x
for o in range(0x0e,0x13): S[o]=1  # 10x/11x
S[0x12]=1  # const/4 11n
S[0x13]=2; S[0x14]=3; S[0x15]=2  # const/16, const, const/high16
S[0x16]=2; S[0x17]=3; S[0x18]=5; S[0x19]=2
S[0x1a]=2; S[0x1b]=3; S[0x1c]=2  # const-string, /jumbo, const-class
S[0x1d]=1; S[0x1e]=1             # monitor-enter/exit
S[0x1f]=2; S[0x20]=2; S[0x21]=1; S[0x22]=2; S[0x23]=2
S[0x24]=3; S[0x25]=3; S[0x26]=3  # filled-new-array(+/range), fill-array-data
S[0x27]=1                        # throw
S[0x28]=1; S[0x29]=2; S[0x2a]=3  # goto, /16, /32
S[0x2b]=3; S[0x2c]=3             # packed/sparse-switch
for o in range(0x2d,0x32): S[o]=2  # cmp
for o in range(0x32,0x3e): S[o]=2  # if tests
for o in range(0x3e,0x44): S[o]=1  # unused
for o in range(0x44,0x52): S[o]=2  # aget/aput
for o in range(0x52,0x5e): S[o]=2  # iget/iput
for o in range(0x5e,0x6e): S[o]=2  # sget/sput
for o in range(0x6e,0x73): S[o]=3  # invoke-kind 35c
S[0x73]=1
for o in range(0x74,0x79): S[o]=4  # invoke-kind/range 45cc
S[0x79]=1; S[0x7a]=1
for o in range(0x7b,0x90): S[o]=1  # unop
for o in range(0x90,0xb0): S[o]=2  # binop 23x
for o in range(0xb0,0xd0): S[o]=1  # binop/2addr
for o in range(0xd0,0xd8): S[o]=2  # binop/lit16
for o in range(0xd8,0xe3): S[o]=2  # binop/lit8
for o in range(0xe3,0xfa): S[o]=1  # unused
S[0xfa]=4; S[0xfb]=4               # invoke-polymorphic(/range)
S[0xfc]=3; S[0xfd]=3               # invoke-custom(/range)
for o in range(0xfe,0x100): S[o]=1

def uleb(off):
    r = 0; s = 0
    while True:
        by = b[off]; off += 1
        r |= (by & 0x7f) << s
        if not (by & 0x80): break
        s += 7
    return r, off

string_ids_size, string_ids_off = struct.unpack_from('<II', b, 56)
type_ids_size, type_ids_off = struct.unpack_from('<II', b, 64)
proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 72)
field_ids_size, field_ids_off = struct.unpack_from('<II', b, 80)
method_ids_size, method_ids_off = struct.unpack_from('<II', b, 88)
class_defs_size, class_defs_off = struct.unpack_from('<II', b, 96)

def get_string(i):
    data_off, = struct.unpack_from('<I', b, string_ids_off + i*4)
    n, off = uleb(data_off)
    end = b.index(b'\x00', off)
    return b[off:end].decode('utf-8', 'replace')

def get_type(i):
    si, = struct.unpack_from('<I', b, type_ids_off + i*4)
    return get_string(si)

def get_method(i):
    cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + i*8)
    shorty, ret_t, params = struct.unpack_from('<III', b, proto_ids_off + proto*12)
    ret = get_type(ret_t)
    return f"{get_type(cls)}.{get_string(name)}:{ret}"

def get_field(i):
    cls, typ, name = struct.unpack_from('<HHI', b, field_ids_off + i*8)
    return f"{get_type(cls)}.{get_string(name)}"

# target string indices
targets = []
if ARG2.startswith('idx='):
    targets = [(int(ARG2[4:]), get_string(int(ARG2[4:])))]
else:
    for i in range(string_ids_size):
        try:
            s = get_string(i)
        except Exception:
            continue
        if ARG2 in s:
            targets.append((i, s))
print(f"string matches: {[(i, repr(s)[:70]) for i, s in targets]}", file=sys.stderr)
tset = set(i for i, _ in targets)

def parse_class_data(off):
    sf, off = uleb(off); inf, off = uleb(off)
    dm, off = uleb(off); vm, off = uleb(off)
    # fields come FIRST: static then instance (field_idx_diff, access_flags)
    fidx = 0
    for _ in range(sf):
        d, off = uleb(off); fidx += d
        acc, off = uleb(off)
    fidx = 0
    for _ in range(inf):
        d, off = uleb(off); fidx += d
        acc, off = uleb(off)
    out = []
    midx = 0
    for _ in range(dm):
        d, off = uleb(off); midx += d
        acc, off = uleb(off); coff, off = uleb(off)
        out.append(('direct', midx, acc, coff))
    midx = 0
    for _ in range(vm):
        d, off = uleb(off); midx += d
        acc, off = uleb(off); coff, off = uleb(off)
        out.append(('virtual', midx, acc, coff))
    return out

def decode(coff):
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', b, coff)
    insns_off = coff + 16
    out = []
    pc = 0
    while pc < insns_size:
        u0, = struct.unpack_from('<H', b, insns_off + pc*2)
        op = u0 & 0xff
        # pseudo payloads
        if u0 == 0x0100:
            size, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            out.append((pc, f"packed-switch-payload size={size}"))
            pc += 4 + 2*size
            continue
        if u0 == 0x0200:
            size, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            out.append((pc, f"sparse-switch-payload size={size}"))
            pc += 2 + 4*size
            continue
        if u0 == 0x0300:
            ew, size = struct.unpack_from('<HH', b, insns_off + (pc+1)*2)
            out.append((pc, f"fill-array-data-payload width={ew} size={size}"))
            pc += 4 + (size*ew + 1)//2
            continue
        txt = f"{op:#04x}"
        if op == 0x1a:
            reg = u0 >> 8
            idx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"const-string v{reg}, {get_string(idx)!r}"
            if idx in tset: txt += "  <<<< HIT"
        elif op == 0x1b:
            reg, = struct.unpack_from('<H', b, insns_off + pc*2 + 2)
            idx, = struct.unpack_from('<I', b, insns_off + (pc+1)*2)
            txt = f"const-string/jumbo v{reg}, {get_string(idx)!r}"
            if idx in tset: txt += "  <<<< HIT"
        elif op in range(0x6e, 0x73):
            midx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cnt = (u0 >> 12) & 0xf
            G = (u0 >> 8) & 0xf
            u2, = struct.unpack_from('<H', b, insns_off + (pc+2)*2)
            regs_list = [u2 & 0xf, (u2 >> 4) & 0xf, (u2 >> 8) & 0xf, (u2 >> 12) & 0xf]
            if cnt == 5:
                regs_list.append(G)
            rl = ['v%d' % r for r in regs_list[:cnt]]
            txt = f"{['invoke-virtual','invoke-super','invoke-direct','invoke-static','invoke-interface'][op-0x6e]} {', '.join(rl)} {get_method(midx)}"
            if op == 0x70 and cnt >= 1 and regs_list[0] == 0:
                pass
        elif op in range(0x74, 0x79):
            midx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cnt = (u0 >> 12) & 0xf
            start, = struct.unpack_from('<H', b, insns_off + (pc+2)*2)
            txt = f"invoke-range v{start}..v{start+cnt-1} {get_method(midx)}"
        elif op in range(0x52, 0x5e):
            fidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"{['iget','iget-wide','iget-object','iget-boolean','iget-byte','iget-char','iget-short','iput','iput-wide','iput-object','iput-boolean','iput-byte'][op-0x52]} {get_field(fidx)}"
        elif op in range(0x5e, 0x6e):
            fidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"{['sget','sget-wide','sget-object','sget-boolean','sget-byte','sget-char','sget-short','sput','sput-wide','sput-object','sput-boolean','sput-byte'][op-0x5e]} {get_field(fidx)}"
        elif op == 0x22:
            tidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"new-instance v{u0>>8}, {get_type(tidx)}"
        elif op == 0x1c:
            tidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"const-class v{u0>>8}, {get_type(tidx)}"
        elif op == 0x1f:
            tidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            txt = f"check-cast v{u0>>8}, {get_type(tidx)}"
        elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
            tgt, = struct.unpack_from('<h', b, insns_off + (pc+1)*2)
            nm = ['if-eq','if-ne','if-lt','if-ge','if-gt','if-le'][op-0x32]
            txt = f"{nm} v{u0>>8}, v{(u0>>12)&0xf} -> {pc+tgt:+d}"
        elif 0x38 <= op <= 0x3d:
            tgt, = struct.unpack_from('<h', b, insns_off + (pc+1)*2)
            nm = ['if-eqz','if-nez','if-ltz','if-gez','if-gtz','if-lez'][op-0x38]
            txt = f"{nm} v{u0>>8} -> {pc+tgt:+d}"
        elif op == 0x28:
            tgt, = struct.unpack_from('<b', b, insns_off + pc*2 + 1)
            txt = f"goto -> {pc+tgt:+d}"
        elif op in (0x2b, 0x2c):
            tgt, = struct.unpack_from('<I', b, insns_off + (pc+1)*2) & 0xffffffff
            tgt_s, = struct.unpack_from('<i', b, insns_off + (pc+1)*2)
            txt = f"{'packed' if op==0x2b else 'sparse'}-switch v{u0>>8}, table@{pc+tgt_s:+d}"
        elif op == 0x27:
            txt = f"throw v{u0>>8}"
        elif op in (0x0e,):
            txt = "return-void"
        elif op in (0x0f, 0x10, 0x11):
            txt = f"return{'-object' if op==0x11 else ''} v{u0>>8}"
        elif op == 0x12:
            txt = f"const/4 v{u0>>8 & 0xf}, {((u0>>12)&0xf)}"
        elif 0x0a <= op <= 0x0d:
            txt = f"move-result{'-object' if op==0x0c else ''} v{u0>>8}"
        out.append((pc, txt))
        pc += S[op]
    return out

hits = 0
for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, src, ann, class_data, sv = struct.unpack_from('<8I', b, off)
    cls = get_type(cls_idx)
    if class_data == 0:
        continue
    dump_this = DUMP and (DUMPCLS in cls)
    if CLSFILTER and CLSFILTER not in cls and not dump_this:
        continue
    for kind, midx, acc, coff in parse_class_data(class_data):
        if coff == 0:
            continue
        mname = get_method(midx)
        dump_m = dump_this and (DUMPMETH is None or DUMPMETH in mname)
        if not dump_m:
            try:
                code = decode(coff)
            except Exception:
                continue
            if not any('HIT' in t for _, t in code):
                continue
        else:
            code = decode(coff)
        hits += 1
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', b, coff)
        print(f"\n===== {cls} ({kind}) {mname}  regs={regs} ins={ins} =====")
        for pc, t in code:
            mark = '>>' if 'HIT' in t else '  '
            print(f"  {mark} {pc:4d}: {t}")

print(f"\nTOTAL methods shown: {hits}")
