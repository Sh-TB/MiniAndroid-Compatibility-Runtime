#!/usr/bin/env python3
"""CONT-46 T3 TELEGRAM: decode Lorg/telegram/ui/ActionBar/o6; forensics.
(a) scan ALL dexes for duplicate class descriptors (R8 collision check)
(b) dump o6 <clinit> + k1 bytecode with resolved field/method names
(c) verify whether the e0 sput-object exists in clinit and which field_idx it uses
Usage: cont46_tg_o6.py [class-Ldesc [method ...]]"""
import sys, zipfile, struct, os

APK = os.environ.get('MA_DEX_APK', '/home/z/my-project/upload/telegram_official.apk')
TARGET_CLASS = sys.argv[1] if len(sys.argv) > 1 else 'Lorg/telegram/ui/ActionBar/o6;'
TARGET_METHODS = sys.argv[2:] if len(sys.argv) > 2 else ['<clinit>', 'k1']

z = zipfile.ZipFile(APK)
ALL_DEXES = [(n, z.read(n)) for n in z.namelist() if n.endswith('.dex')]
print(f"loaded {len(ALL_DEXES)} dex files")

# Raw-byte opcode table VERIFIED against the engine's dalvik_engine.h
# (which passes real-APK regression walls) — sput family 0x67-0x6D, NOT 0x6A-0x6D.
OPS = {0x00:'nop',0x01:'move',0x02:'move/from16',0x03:'move/16',0x04:'move-wide',
       0x05:'move-wide/from16',0x06:'move-wide/16',0x07:'move-object',
       0x08:'move-object/from16',0x09:'move-object/16',0x0a:'move-result',
       0x0b:'move-result-wide',0x0c:'move-result-object',0x0d:'move-exception',
       0x0e:'return-void',0x0f:'return',0x10:'return-wide',0x11:'return-object',
       0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',
       0x16:'const-wide/16',0x17:'const-wide/32',0x18:'const-wide',
       0x19:'const-wide/high16',0x1a:'const-string',0x1b:'const-string/jumbo',
       0x1c:'const-class',0x1d:'monitor-enter',0x1e:'monitor-exit',
       0x1f:'check-cast',0x20:'instance-of',0x21:'array-length',0x22:'new-instance',
       0x23:'new-array',0x24:'filled-new-array',0x25:'filled-new-array/range',
       0x26:'fill-array-data',0x27:'throw',0x28:'goto',0x29:'goto/16',0x2a:'goto/32',
       0x2b:'packed-switch',0x2c:'sparse-switch',0x2d:'cmpl-float',0x2e:'cmpg-float',
       0x2f:'cmpl-double',0x30:'cmpg-double',0x31:'cmp-long',
       0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le',
       0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',
       0x3d:'if-lez',0x44:'aget',0x45:'aget-wide',0x46:'aget-object',
       0x47:'aget-boolean',0x48:'aget-byte',0x49:'aget-char',0x4a:'aget-short',
       0x4b:'aput',0x4c:'aput-wide',0x4d:'aput-object',0x4e:'aput-boolean',
       0x4f:'aput-byte',0x50:'aput-char',0x51:'aput-short',0x52:'iget',
       0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',0x56:'iget-byte',
       0x57:'iget-char',0x58:'iget-short',0x59:'iput',0x5a:'iput-wide',
       0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',0x5e:'iput-char',
       0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',0x62:'sget-object',
       0x63:'sget-boolean',0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',
       0x67:'sput',0x68:'sput-wide',0x69:'sput-object',0x6a:'sput-boolean',
       0x6b:'sput-byte',0x6c:'sput-char',0x6d:'sput-short',
       0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
       0x71:'invoke-static',0x72:'invoke-interface',
       0x74:'invoke-virtual/range',0x75:'invoke-super/range',0x76:'invoke-direct/range',
       0x77:'invoke-static/range',0x78:'invoke-interface/range',
       0xfa:'invoke-polymorphic',0xfb:'invoke-polymorphic/range'}

# Dalvik instruction widths in 16-bit code units, keyed by opcode.
W1 = {0x01,0x04,0x07} | set(range(0x0a,0x13)) | {0x1d,0x1e,0x21,0x27,0x28} | set(range(0x7b,0xb0))
W2 = {0x02,0x05,0x08, 0x13,0x15,0x16,0x19,0x1a,0x1c, 0x1f,0x20,0x22,0x23} | set(range(0x29,0x2d)) | set(range(0x32,0x3e)) | set(range(0x44,0x6e)) | set(range(0xd0,0xe3)) | {0xfe,0xff}
W3 = {0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c} | set(range(0x6e,0x73)) | set(range(0x74,0x79)) | {0xfc,0xfd}
W4 = {0xfa,0xfb}
W5 = {0x18}

def insn_width(op, b, insns_off, i, insns_size):
    if op == 0x00:
        # nop or payload: check the NEXT code unit
        if i + 1 < insns_size:
            nxt = b[insns_off + 2*(i+1)] | (b[insns_off + 2*(i+1)+1] << 8)
            if nxt == 0x0100:  # packed-switch-payload: size=4+2*size units
                size = u2(b, insns_off + 2*i + 4)
                return 4 + 2*size
            if nxt == 0x0200:  # sparse-switch-payload: size=2+4*size
                size = u2(b, insns_off + 2*i + 2)
                return 2 + 4*size
            if nxt == 0x0300:  # fill-array-data-payload: 4 + (elem_width*size+1)/2
                ew = u2(b, insns_off + 2*i + 2)
                sz = u4(b, insns_off + 2*i + 4)
                return 4 + (ew*sz + 1)//2
        return 1
    if op in W1: return 1
    if op in W2: return 2
    if op in W3: return 3
    if op in W4: return 4
    if op in W5: return 5
    return 2  # unknown/odex: assume 2

def u4(b,o): return struct.unpack_from('<I',b,o)[0]
def u2(b,o): return struct.unpack_from('<H',b,o)[0]

def parse_dex(name, b):
    """return (field_ids, method_ids, string_ids, class_defs, header)"""
    string_ids_size, string_ids_off = u4(b,0x38), u4(b,0x3c)
    type_ids_size, type_ids_off = u4(b,0x40), u4(b,0x44)
    proto_size, proto_off = u4(b,0x48), u4(b,0x4c)
    field_ids_size, field_ids_off = u4(b,0x50), u4(b,0x54)
    method_ids_size, method_ids_off = u4(b,0x58), u4(b,0x5c)
    class_defs_size, class_defs_off = u4(b,0x60), u4(b,0x64)
    def get_str(si):
        if si >= string_ids_size: return f"<str{si}>"
        off = u4(b, string_ids_off + 4*si)
        # uleb128 length then bytes
        n=0; shift=0; p=off
        while True:
            x=b[p]; n |= (x&0x7f)<<shift; p+=1
            if not (x&0x80): break
            shift+=7
        return b[p:p+n].decode('utf-8','replace')
    def get_type(ti):
        if ti >= type_ids_size: return f"<type{ti}>"
        return get_str(u4(b, type_ids_off + 4*ti))
    fields=[]
    for i in range(field_ids_size):
        o = field_ids_off + 8*i
        class_idx = u2(b,o); type_idx=u2(b,o+2); name_idx=u4(b,o+4)
        fields.append((get_type(class_idx), get_type(type_idx), get_str(name_idx)))
    methods=[]
    for i in range(method_ids_size):
        o = method_ids_off + 8*i
        class_idx = u2(b,o); proto_idx=u2(b,o+2); name_idx=u4(b,o+4)
        methods.append((get_type(class_idx), get_str(name_idx)))
    classes=[]
    for i in range(class_defs_size):
        o = class_defs_off + 32*i
        class_idx=u4(b,o); access=u4(b,o+4); super_idx=u4(b,o+8)
        src=u4(b,o+16); ann=u4(b,o+20); cd_off=u4(b,o+24)
        classes.append((get_type(class_idx), cd_off))
    return fields, methods, classes

def parse_class_data(b, cd_off):
    """return (static_fields[(idx,acc,off)], instance_fields, direct_methods, virtual_methods)"""
    p = cd_off
    def uleb():
        nonlocal p
        n=0;shift=0
        while True:
            x=b[p]; n |= (x&0x7f)<<shift; p+=1
            if not (x&0x80): break
            shift+=7
        return n
    sf_n = uleb(); inf_n = uleb(); dm_n = uleb(); vm_n = uleb()
    def field_list(n):
        out=[]; fidx=0
        for _ in range(n):
            d=uleb(); fidx+=d; acc=uleb(); out.append((fidx,acc))
        return out
    sfields = field_list(sf_n); ifields = field_list(inf_n)
    def meth_list(n):
        out=[]; midx=0
        for _ in range(n):
            d=uleb(); midx+=d; acc=uleb(); code_off=uleb()
            out.append((midx,acc,code_off))
        return out
    dmethods = meth_list(dm_n); vmethods = meth_list(vm_n)
    return sfields, ifields, dmethods, vmethods

def parse_code_item(b, code_off, fields, methods):
    regs = u2(b, code_off); ins=u2(b,code_off+2); outs=u2(b,code_off+4)
    insns_size = u4(b, code_off+12)
    insns_off = code_off + 16
    lines=[]
    i=0
    while i < insns_size:
        pcu = i
        op = b[insns_off + 2*i]
        w = OPS.get(op, f'op-{op:#04x}')
        units = insn_width(op, b, insns_off, i, insns_size)
        desc = w
        try:
            reg_byte = b[insns_off+2*i+1]
            arg16 = u2(b, insns_off+2*i+2) if units>=2 else None
            arg32 = u4(b, insns_off+2*i+2) if units>=3 else None
        except Exception:
            arg16 = arg32 = None
        if units == 1:
            nibA = (reg_byte >> 4) & 0xf
            nibB = reg_byte & 0xf
            if op == 0x12:
                v = b[insns_off+2*i+1]
                desc = f"const/4 v{v&0xf}, #{(v>>4)&0xf if ((v>>4)&0xf)<8 else ((v>>4)&0xf)-16}"
            elif op in (0x01,0x04,0x07):
                desc = f"{w} v{nibA}, v{nibB}"
            elif op in (0x0a,0x0b,0x0c,0x0d,0x0f,0x10,0x11,0x1d,0x1e,0x27,0x21):
                desc = f"{w} v{reg_byte:#x}"
            elif op == 0x28:
                desc = f"goto {reg_byte if reg_byte<0x80 else reg_byte-0x100:+d}"
            elif op == 0x00 and i+1 < insns_size:
                nxt = b[insns_off+2*(i+1)] | (b[insns_off+2*(i+1)+1] << 8)
                if nxt in (0x0100,0x0200,0x0300):
                    desc = f"{w}-payload-{nxt:#06x}"
        elif units == 2:
            if op in (0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
                if arg16 < len(fields):
                    cd, td, fn = fields[arg16]
                    vAA = reg_byte
                    if op >= 0x67:
                        desc = f"{w} v{vAA:#x} <- {cd}.{fn}:{td}"
                    else:
                        desc = f"{w} v{vAA:#x}, {cd}.{fn}:{td}"
                else:
                    desc = f"{w} field@{arg16}"
            elif op in (0x6e,0x6f,0x70,0x71,0x72):
                # 35c: A|G|op BBBB FEDC — regs C,D,E,F,G from the THIRD unit
                cnt = (reg_byte >> 4) & 0xf
                fedc = u2(b, insns_off+2*i+4)
                rC = fedc & 0xf; rD = (fedc >> 4) & 0xf; rE = (fedc >> 8) & 0xf
                rF = (fedc >> 12) & 0xf; rG = reg_byte & 0xf
                regs_list = [rC,rD,rE,rF,rG][:cnt]
                regs_s = ", ".join(f"v{r}" for r in regs_list)
                if arg16 < len(methods):
                    cd, mn = methods[arg16]
                    desc = f"{w} {{{regs_s}}}, {cd}.{mn}"
                else:
                    desc = f"{w} method@{arg16}"
            elif op == 0x1a:
                desc = f"const-string v{reg_byte:#x}, str@{arg16}"
            elif op in (0x1c,0x1f,0x22):
                desc = f"{w} v{reg_byte:#x}, type@{arg16:#x}"
            elif op == 0x20:
                nibA = (b[insns_off+2*i+1] >> 4) & 0xf
                desc = f"instance-of v{nibA}, v{reg_byte&0xf}, type@{arg16:#x}"
            elif op == 0x23:
                nibA = (b[insns_off+2*i+1] >> 4) & 0xf
                desc = f"new-array v{nibA}, v{reg_byte&0xf}, type@{arg16:#x}"
            elif op in (0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,0x50,0x51):
                # 23x: vAA, vBB, vCC
                vBB = b[insns_off+2*i+2]; vCC = b[insns_off+2*i+3]
                desc = f"{w} v{reg_byte:#x} = v{vBB:#x}[v{vCC:#x}]"
            elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f):
                if arg16 < len(fields):
                    cd, td, fn = fields[arg16]
                    nibA = (b[insns_off+2*i+1] >> 4) & 0xf
                    if op >= 0x59:
                        desc = f"{w} v{nibA} <- v{reg_byte&0xf}, {cd}.{fn}"
                    else:
                        desc = f"{w} v{nibA}, v{reg_byte&0xf}, {cd}.{fn}"
                else:
                    desc = f"{w} field@{arg16}"
            elif op == 0x13 or op == 0x16:
                s = arg16 if arg16 < 0x8000 else arg16-0x10000
                desc = f"{w} v{reg_byte:#x}, #{s}"
            elif op == 0x15:
                desc = f"const/high16 v{reg_byte:#x}, #{arg16:#x}0000"
            elif op == 0x29:
                s = arg16 if arg16 < 0x8000 else arg16-0x10000
                desc = f"goto/16 {s:+d}"
            elif op in range(0x38,0x3e):
                s = arg16 if arg16 < 0x8000 else arg16-0x10000
                desc = f"{w} v{reg_byte:#x}, ->{s:+d}"
            elif op in range(0x32,0x38):
                s = arg16 if arg16 < 0x8000 else arg16-0x10000
                nibA = (b[insns_off+2*i+1] >> 4) & 0xf
                desc = f"{w} v{nibA}, v{reg_byte&0xf}, ->{s:+d}"
            elif op == 0x12:
                pass
        elif units >= 3:
            if op in (0x74,0x75,0x76,0x77,0x78):
                # 3rc: AA|op BBBB CCCC — count=reg_byte, first reg=arg32(u2@+4)
                cnt = reg_byte
                first = u2(b, insns_off+2*i+4)
                regs_s = f"v{first:#x}..v{first+cnt-1:#x}" if cnt else "{}"
                if arg32 < len(methods):
                    cd, mn = methods[arg32]
                    desc = f"{w} {{{regs_s}}}, {cd}.{mn}"
                else:
                    desc = f"{w} method@{arg32}"
            elif op == 0x1b:
                desc = f"const-string/jumbo v{reg_byte:#x}, str@{arg32}"
            elif op == 0x14:
                desc = f"const v{reg_byte:#x}, #{arg32:#x}"
            elif op == 0x18:
                arg64 = struct.unpack_from('<Q', b, insns_off+2*i+2)[0]
                desc = f"const-wide v{reg_byte:#x}, #{arg64:#x}"
            elif op in (0x2b,0x2c,0x26):
                desc = f"{w} v{reg_byte:#x}, payload@{pcu + (arg32 if arg32<0x80000000 else arg32-0x100000000):+d}"
            elif op == 0x2a:
                desc = f"goto/32 {arg32 if arg32<0x80000000 else arg32-0x100000000:+d}"
            elif op == 0xfa:
                arg3 = u2(b, insns_off+2*i+6)
                if arg32 < len(methods):
                    cd, mn = methods[arg32]
                    desc = f"invoke-polymorphic {cd}.{mn} proto@{arg3:#x}"
                units = 4
        lines.append((pcu, desc, units))
        i += units
    return regs, ins, outs, lines

# ── (a) duplicate class descriptor scan across dexes ──
seen = {}
for name, b in ALL_DEXES:
    fields, methods, classes = parse_dex(name, b)
    for cd, _ in classes:
        seen.setdefault(cd, []).append(name)
dups = {k:v for k,v in seen.items() if len(set(v))>1}
print(f"total class descriptors: {len(seen)}, duplicated across dexes: {len(dups)}")
for k in list(dups)[:8]:
    print(f"  DUP {k} in {dups[k]}")
if TARGET_CLASS in dups:
    print(f"  !! TARGET CLASS {TARGET_CLASS} IS DUPLICATED: {dups[TARGET_CLASS]}")

# ── (a2) FIELD-WRITER CENSUS: every sput-object/sput of TARGET_CLASS.<field> across ALL dexes ──
import re
if len(sys.argv) > 2 and sys.argv[2].startswith('!'):
    FIELD = sys.argv[3] if len(sys.argv) > 3 else 'e0'
    print(f"\n=== writer census: {TARGET_CLASS}.{FIELD} ===")
    for name, b in ALL_DEXES:
        fields, methods, classes = parse_dex(name, b)
        # map field_idx -> matching
        fidxs = [i for i,(cd,td,fn) in enumerate(fields) if cd==TARGET_CLASS and fn==FIELD]
        if not fidxs: continue
        clsmap = {cd: off for cd, off in classes}
        for cd, off in classes:
            try:
                sfields, ifields, dmethods, vmethods = parse_class_data(b, off)
            except Exception:
                continue
            for kind, (midx, acc, code_off) in [('d',m) for m in dmethods]+[('v',m) for m in vmethods]:
                if code_off == 0: continue
                try:
                    _, mn = methods[midx]
                    regs, ins, outs, lines = parse_code_item(b, code_off, fields, methods)
                except Exception:
                    continue
                for pcu, desc, _u in lines:
                    if (f'.{FIELD}:' in desc and f'{TARGET_CLASS}.' in desc and
                        (desc.startswith('sput-object') or desc.startswith('sput ') or
                         desc.startswith('sget-object') or desc.startswith('sget '))):
                        op = desc.split()[0]
                        if op.startswith('sput'):
                            print(f"  WRITER {name} {cd}.{mn} pc={pcu:#06x}: {desc}")
                        else:
                            print(f"  READER {name} {cd}.{mn} pc={pcu:#06x}: {desc}")
    sys.exit(0)

# ── (b)+(c) decode target class ──
for name, b in ALL_DEXES:
    fields, methods, classes = parse_dex(name, b)
    clsmap = {cd: off for cd, off in classes}
    if TARGET_CLASS not in clsmap:
        continue
    print(f"\n=== {TARGET_CLASS} found in {name} ===")
    sfields, ifields, dmethods, vmethods = parse_class_data(b, clsmap[TARGET_CLASS])
    print(f"static fields ({len(sfields)}):")
    for fidx, acc in sfields:
        cd, td, fn = fields[fidx]
        print(f"  field@{fidx} {cd}.{fn}:{td} acc={acc:#x}")
    want = set(TARGET_METHODS)
    all_m = [('direct', m) for m in dmethods] + [('virtual', m) for m in vmethods]
    for kind, (midx, acc, code_off) in all_m:
        cd, mn = methods[midx]
        if mn not in want:
            continue
        print(f"\n--- {kind} method {cd}.{mn} acc={acc:#x} code_off={code_off:#x} ---")
        if code_off == 0:
            print("  (abstract/native)")
            continue
        regs, ins, outs, lines = parse_code_item(b, code_off, fields, methods)
        print(f"  regs={regs} ins={ins} outs={outs}")
        for pcu, desc, _ in lines:
            print(f"  {pcu:04x}: {desc}")
    break
else:
    print(f"TARGET {TARGET_CLASS} NOT FOUND in any dex")
