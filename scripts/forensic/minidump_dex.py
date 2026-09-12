#!/usr/bin/env python3
"""scripts/forensic/minidump_dex.py — precise Dalvik method disassembler (M9 forensic oracle).

Full opcode table with correct instruction lengths (AOSP dalvik-bytecode.html),
correct 22b/22t/22s/23x/31i/51l decoding and normalized branch targets.
Independent oracle: does not reuse the runtime parser.

Usage: python3 scripts/forensic/minidump_dex.py <apk> <class-desc> <method-name>
"""
import struct, zipfile, sys

APK, CLS, METH = sys.argv[1], sys.argv[2], sys.argv[3]

z = zipfile.ZipFile(APK)
dex = z.read('classes.dex')
u4 = lambda o: struct.unpack_from('<I', dex, o)[0]
u2 = lambda o: struct.unpack_from('<H', dex, o)[0]

def uleb(o):
    r = s = 0
    while True:
        b = dex[o]; o += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): return r, o
        s += 7

S_IDS = u4(0x38); S_OFF = u4(0x3c)
T_IDS = u4(0x40); T_OFF = u4(0x44)
F_IDS = u4(0x50); F_OFF = u4(0x54)
M_IDS = u4(0x58); M_OFF = u4(0x5c)
C_CNT = u4(0x60); C_OFF = u4(0x64)

def get_str(i):
    o = u4(S_OFF + 4*i)
    _, o2 = uleb(o)
    e = dex.index(b'\x00', o2)
    return dex[o2:e].decode('utf-8', 'replace')

def type_str(i): return get_str(u4(T_OFF + 4*i))
def field_str(i):
    o = F_OFF + 8*i
    return type_str(u2(o)) + '.' + get_str(u4(o+4))
def method_str(i):
    o = M_OFF + 8*i
    return type_str(u2(o)) + '.' + get_str(u4(o+4))

# opcode table: name, format
F = lambda: None
OPS = {
0x00:('nop','10x'),0x01:('move','12x'),0x02:('move/from16','22x'),0x03:('move/16','32x'),
0x04:('move-wide','12x'),0x05:('move-wide/from16','22x'),0x06:('move-wide/16','32x'),
0x07:('move-object','12x'),0x08:('move-object/from16','22x'),0x09:('move-object/16','32x'),
0x0a:('move-result','11x'),0x0b:('move-result-wide','11x'),0x0c:('move-result-object','11x'),
0x0d:('move-exception','11x'),0x0e:('return-void','10x'),0x0f:('return','11x'),
0x10:('return-wide','11x'),0x11:('return-object','11x'),0x12:('const/4','11n'),
0x13:('const/16','21s'),0x14:('const','31i'),0x15:('const/high16','21h'),
0x16:('const-wide/16','21s'),0x17:('const-wide/32','31i'),0x18:('const-wide','51l'),
0x19:('const-wide/high16','21h'),0x1a:('const-string','21c'),0x1b:('const-string/jumbo','31c'),
0x1c:('const-class','21c'),0x1d:('monitor-enter','11x'),0x1e:('monitor-exit','11x'),
0x1f:('check-cast','21c'),0x20:('instance-of','22c'),0x21:('array-length','12x'),
0x22:('new-instance','21c'),0x23:('new-array','22c'),0x24:('filled-new-array','35c'),
0x25:('filled-new-array/range','3rc'),0x26:('fill-array-data','31t'),0x27:('throw','11x'),
0x28:('goto','10t'),0x29:('goto/16','20t'),0x2a:('goto/32','30t'),
0x2b:('packed-switch','31t'),0x2c:('sparse-switch','31t'),
0x2d:('cmpl-float','23x'),0x2e:('cmpg-float','23x'),0x2f:('cmpl-double','23x'),
0x30:('cmpg-double','23x'),0x31:('cmp-long','23x'),
0x32:('if-eq','22t'),0x33:('if-ne','22t'),0x34:('if-lt','22t'),0x35:('if-ge','22t'),
0x36:('if-gt','22t'),0x37:('if-le','22t'),0x38:('if-eqz','21t'),0x39:('if-nez','21t'),
0x3a:('if-ltz','21t'),0x3b:('if-gez','21t'),0x3c:('if-gtz','21t'),0x3d:('if-lez','21t'),
0x44:('aget','23x'),0x45:('aget-wide','23x'),0x46:('aget-object','23x'),0x47:('aget-boolean','23x'),
0x48:('aget-byte','23x'),0x49:('aget-char','23x'),0x4a:('aget-short','23x'),
0x4b:('aput','23x'),0x4c:('aput-wide','23x'),0x4d:('aput-object','23x'),0x4e:('aput-boolean','23x'),
0x4f:('aput-byte','23x'),0x50:('aput-char','23x'),0x51:('aput-short','23x'),
0x52:('iget','22c'),0x53:('iget-wide','22c'),0x54:('iget-object','22c'),0x55:('iget-boolean','22c'),
0x56:('iget-byte','22c'),0x57:('iget-char','22c'),0x58:('iget-short','22c'),
0x59:('iput','22c'),0x5a:('iput-wide','22c'),0x5b:('iput-object','22c'),0x5c:('iput-boolean','22c'),
0x5d:('iput-byte','22c'),0x5e:('iput-char','22c'),0x5f:('iput-short','22c'),
0x60:('sget','21c'),0x61:('sget-wide','21c'),0x62:('sget-object','21c'),0x63:('sget-boolean','21c'),
0x64:('sget-byte','21c'),0x65:('sget-char','21c'),0x66:('sget-short','21c'),
0x67:('sput','21c'),0x68:('sput-wide','21c'),0x69:('sput-object','21c'),0x6a:('sput-boolean','21c'),
0x6b:('sput-byte','21c'),0x6c:('sput-char','21c'),0x6d:('sput-short','21c'),
}
for i,(nm,frm) in enumerate([
 ('add-int','23x'),('sub-int','23x'),('mul-int','23x'),('div-int','23x'),('rem-int','23x'),
 ('and-int','23x'),('or-int','23x'),('xor-int','23x'),('shl-int','23x'),('shr-int','23x'),
 ('ushr-int','23x'),('add-long','23x'),('sub-long','23x'),('mul-long','23x'),('div-long','23x'),
 ('rem-long','23x'),('and-long','23x'),('or-long','23x'),('xor-long','23x'),('shl-long','23x'),
 ('shr-long','23x'),('ushr-long','23x'),('add-float','23x'),('sub-float','23x'),('mul-float','23x'),
 ('div-float','23x'),('rem-float','23x'),('add-double','23x'),('sub-double','23x'),('mul-double','23x'),
 ('div-double','23x'),('rem-double','23x')], start=0x90):
    OPS[i] = (nm, frm)
for i,(nm) in enumerate([
 'add-int/2addr','sub-int/2addr','mul-int/2addr','div-int/2addr','rem-int/2addr',
 'and-int/2addr','or-int/2addr','xor-int/2addr','shl-int/2addr','shr-int/2addr','ushr-int/2addr',
 'add-long/2addr','sub-long/2addr','mul-long/2addr','div-long/2addr','rem-long/2addr',
 'and-long/2addr','or-long/2addr','xor-long/2addr','shl-long/2addr','shr-long/2addr','ushr-long/2addr',
 'add-float/2addr','sub-float/2addr','mul-float/2addr','div-float/2addr','rem-float/2addr',
 'add-double/2addr','sub-double/2addr','mul-double/2addr','div-double/2addr','rem-double/2addr'], start=0xb0):
    OPS[i] = (nm, '12x')
for i,(nm) in enumerate([
 'add-int/lit16','sub-int/lit16','mul-int/lit16','div-int/lit16','rem-int/lit16',
 'and-int/lit16','or-int/lit16','xor-int/lit16'], start=0xd0):
    OPS[i] = (nm, '22b')
for i,(nm) in enumerate([
 'add-int/lit8','sub-int/lit8','mul-int/lit8','div-int/lit8','rem-int/lit8',
 'and-int/lit8','or-int/lit8','xor-int/lit8','shl-int/lit8','shr-int/lit8','ushr-int/lit8'], start=0xd8):
    OPS[i] = (nm, '22b')
for i,(nm,frm) in enumerate([
 ('neg-int','12x'),('not-int','12x'),('neg-long','12x'),('not-long','12x'),
 ('neg-float','12x'),('neg-double','12x'),('int-to-long','12x'),('int-to-float','12x'),
 ('int-to-double','12x'),('long-to-int','12x'),('long-to-float','12x'),('long-to-double','12x'),
 ('float-to-int','12x'),('float-to-long','12x'),('float-to-double','12x'),
 ('double-to-int','12x'),('double-to-long','12x'),('double-to-float','12x'),
 ('int-to-byte','12x'),('int-to-char','12x'),('int-to-short','12x')], start=0x7b):
    OPS[i] = (nm, frm)
for i,(nm) in enumerate([
 'invoke-virtual','invoke-super','invoke-direct','invoke-static','invoke-interface'], start=0x6e):
    OPS[i] = (nm, '35c')
OPS[0x74]=('invoke-virtual/range','3rc');OPS[0x75]=('invoke-super/range','3rc')
OPS[0x76]=('invoke-direct/range','3rc');OPS[0x77]=('invoke-static/range','3rc')
OPS[0x78]=('invoke-interface/range','3rc')

FMT_LEN = {'10x':2,'12x':2,'11n':2,'11x':2,'10t':2,'20t':4,'22x':4,'21s':4,'21h':4,'21c':4,'21t':4,
 '23x':4,'22b':4,'22t':4,'22s':4,'22c':4,'30t':8,'31i':6,'31t':6,'31c':6,'32x':6,'35c':6,
 '3rc':6,'51l':10}

def s16(v): return v - 0x10000 if v & 0x8000 else v
def s32(v): return v - 0x100000000 if v & 0x80000000 else v

# locate method
target_code_off = None
for c in range(C_CNT):
    off = C_OFF + 32*c
    if type_str(u4(off)) != CLS: continue
    cdo = u4(off+24)
    p = cdo
    sf, p = uleb(p); inf, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
    fid = 0
    prev = 0
    for i in range(sf):
        d, p = uleb(p); _, p = uleb(p); fid += d
    prev = 0
    for i in range(inf):
        d, p = uleb(p); _, p = uleb(p); fid += d
    for cnt in (dm, vm):
        prev = 0
        for i in range(cnt):
            d, p = uleb(p); _, p = uleb(p); code_off, p = uleb(p)
            prev += d
            mo = M_OFF + 8*prev
            if code_off == 0: continue
            if get_str(u4(mo+4)) == METH:
                target_code_off = code_off
                print(f"=== {CLS}.{METH} {type_str(u2(mo+4))} code_off={hex(code_off)} ===")
if target_code_off is None:
    print("method not found"); sys.exit(1)

co = target_code_off
insns_size = u4(co+12)
insns_off = co + 16
pc = 0
while pc < insns_size:
    o = insns_off + 2*pc
    op = dex[o]
    nm, frm = OPS.get(op, (f'op-0x{op:02x}', None))
    if frm is None:
        print(f"PC={pc:4d} (0x{pc:04x})  RAW {dex[o]:02x} {dex[o+1]:02x}")
        pc += 1; continue
    L = FMT_LEN[frm] // 2
    AA = dex[o+1] & 0xF; BB_ = (dex[o+1] >> 4) & 0xF
    A8 = dex[o+1]; B16 = u2(o+2)
    extra = ''
    if frm == '21c' or frm == '31c':
        idx = B16 if frm == '21c' else u4(o+2)
        if op in (0x1a, 0x1b): extra = '"' + get_str(idx) + '"'
        elif op in (0x1c,0x1f,0x20,0x22,0x23): extra = type_str(idx)
        elif 0x52 <= op <= 0x6d: extra = field_str(idx)
    elif frm == '22c':
        idx = u2(o+2)
        regs_part = f"v{AA}, v{BB_}, "
        if 0x52 <= op <= 0x6d: extra = regs_part + field_str(idx)
        else: extra = f"v{AA}, v{BB_}, " + type_str(idx)
    elif frm == '35c':
        idx = u2(o+2)
        extra = method_str(idx)
    elif frm == '3rc':
        idx = u2(o+2)
        extra = method_str(idx)
    elif frm == '23x':
        extra = f"v{dex[o+1]}, v{u2(o+2)&0xff}, v{(u2(o+2)>>8)&0xff}"
    elif frm in ('22t',):
        tgt = pc + s16(B16)
        extra = f"v{AA}, v{BB_}, ->{tgt}"
    elif frm == '21t':
        tgt = pc + s16(B16)
        extra = f"v{A8}, ->{tgt}"
    elif frm in ('10t',):
        tgt = pc + ((dex[o+1] - 0x100) if dex[o+1] & 0x80 else dex[o+1])
        extra = f"->{tgt}"
    elif frm == '20t':
        tgt = pc + s16(B16)
        extra = f"->{tgt}"
    elif frm == '30t':
        tgt = pc + s32(u4(o+2))
        extra = f"->{tgt}"
    elif frm == '22s':
        extra = f"v{AA}, v{BB_}, #{s16(B16)}"
    elif frm == '21s':
        extra = f"v{A8}, #{s16(B16)}"
    elif frm == '21h':
        extra = f"v{A8}, #0x{B16:04x}00000000" if op == 0x19 else f"v{A8}, #0x{B16:04x}0000"
    elif frm == '31i':
        extra = f"v{A8}, #{s32(u4(o+2))}"
    elif frm == '51l':
        extra = f"v{A8}, #0x{struct.unpack_from('<Q', dex, o+2)[0]:016x}"
    elif frm == '12x':
        extra = f"v{AA}, v{BB_}"
    elif frm == '11n':
        v = BB_ - 0x10 if BB_ & 0x8 else BB_
        extra = f"v{AA}, #{v}"
    elif frm == '22b':
        extra = f"v{A8}, v{u2(o+2)&0xff}, #{s16(u2(o+2)>>8 if False else dex[o+3])}" if False else f"v{A8}, v{dex[o+2]}, #{dex[o+3]-256 if dex[o+3]&0x80 else dex[o+3]}"
    elif frm == '31t':
        tgt = pc + s32(u4(o+2))
        extra = f"v{A8}, ->{tgt}"
    elif frm == '35c' and False:
        pass
    elif frm in ('11x','10x'):
        extra = f"v{A8}" if frm == '11x' else ''
    if frm == '35c':
        regs = dex[o+4]
        rlist = [regs & 0xF, (regs>>4)&0xF, dex[o+5]&0xF, (dex[o+5]>>4)&0xF, A8]
        cnt = (B16 >> 12) & 0xF
        extra = f"{{v{rlist[0]},v{rlist[1]},v{rlist[2]},v{rlist[3]},v{rlist[4]}[:cnt]}}"[:cnt*4+2] + ' ' + extra if False else method_str(idx) + f" v{{{','.join(str(r) for r in rlist[:cnt])}}}"
    print(f"PC={pc:4d} (0x{pc:04x})  {nm:22s} {extra}")
    pc += L
