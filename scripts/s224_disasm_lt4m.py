#!/usr/bin/env python3
"""S224: disassemble Lt4;.m around the UP-NPE PCs (368-390) — find the empty-list
producer + the null receiver's getClass call. Also dump Lt4;.z and the MotionEvent
getter readers near the touch path."""
import struct, zipfile, sys

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
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

str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
f_size, f_off = struct.unpack_from("<2I", dex, 0x50)
m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)

def str_at(si):
    if si >= str_size: return f"str@{si}??"
    off = str_off_arr[si]
    n, o = uleb(dex, off)
    raw = dex[o:o+n]
    out = []
    i = 0
    while i < len(raw):
        b = raw[i]
        if b < 0x80: out.append(chr(b)); i += 1
        elif b < 0xE0: out.append(chr(((b & 0x1F) << 6) | (raw[i+1] & 0x3F))); i += 2
        else: out.append(chr(((b & 0x0F) << 12) | ((raw[i+1] & 0x3F) << 6) | (raw[i+2] & 0x3F))); i += 3
    return ''.join(out)

type_at = lambda ti: str_at(struct.unpack_from('<I', dex, type_off + ti*4)[0]) if ti < type_size else f"type@{ti}??"

def field_at(fi):
    ci, ti, ni = struct.unpack_from('<HHI', dex, f_off + fi*8)
    return f"{type_at(ci)}.{str_at(ni)}:{type_at(ti)}"

def method_at(mi):
    ci, pi, ni = struct.unpack_from('<HHI', dex, m_off + mi*8)
    return f"{type_at(ci)}.{str_at(ni)}"

# find class Lt4;
target = sys.argv[1] if len(sys.argv) > 1 else 'Lt4;'
want_method = sys.argv[2] if len(sys.argv) > 2 else 'm'

cls_info = None
for ci in range(c_size):
    base = c_off + ci * 32
    class_idx, access, superclass, interfaces_off, source, ann, cd_off, sv = struct.unpack_from('<8I', dex, base)
    if type_at(class_idx) == target:
        cls_info = (cd_off, superclass)
        print(f"{target} found: cd_off=0x{cd_off:x} super={type_at(superclass)}")
        break
if not cls_info:
    print(f"{target} NOT FOUND"); sys.exit(1)

cd_off = cls_info[0]
o = cd_off
fidx = 0
nsf, o = uleb(dex, cd_off); o = o
for _ in range(nsf):
    fd, o = uleb(dex, o); fidx += fd
    acc, o = uleb(dex, o)
nif = o
cnt, o = uleb(dex, o)
for _ in range(cnt):
    fd, o = uleb(dex, o); fidx += fd
    acc, o = uleb(dex, o)
midx = 0
ndm, o = uleb(dex, o)
for _ in range(ndm):
    md, o = uleb(dex, o); midx += md
    acc, o = uleb(dex, o)
    co, o = uleb(dex, o)
nvm, o = uleb(dex, o)
methods = []
for _ in range(nvm):
    md, o = uleb(dex, o); midx += md
    acc, o = uleb(dex, o)
    co, o = uleb(dex, o)
    methods.append((midx, co))

# code_item parse for the wanted method: find method whose name matches
found = False
for mi, co in methods:
    mn = method_at(mi)
    short = mn.split('.')[-1].split('(')[0]
    if short != want_method: continue
    found = True
    # code_item: registers u16, ins u16, outs u16, tries u16, debug u32, insns u32, insns...
    regs, ins, outs, tries = struct.unpack_from('<4H', dex, co)
    debug_off, insns_size = struct.unpack_from('<2I', dex, co + 8)
    print(f"{mn} regs={regs} ins={ins} outs={outs} insns={insns_size} tries={tries}")
    pc = 0
    i = co + 16
    end = i + insns_size * 2
    while i < end:
        op = dex[i] if False else (dex[i] & 0xFF)
        # read code unit
        unit = struct.unpack_from('<H', dex, i)[0]
        opc = unit & 0xFF
        if opc == 0x00 and unit == 0x0100:
            pass
        desc = ''
        if opc in (0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60):
            fidx2 = struct.unpack_from('<H', dex, i+2)[0]
            desc = field_at(fidx2)
            print(f"  {pc:#06x}: {['iget','iget-wide','iget-object','iget-boolean','iget-byte','iget-char','iget-short','iput','iput-wide','iput-object','iput-boolean','iput-byte','iput-short','iput-char','sget'][min(opc-0x52,14)] if opc>=0x52 else '?'} {desc}")
            i += 4; pc += 2
        elif 0x6e <= opc <= 0x72 or 0x74 <= opc <= 0x78:
            midx2 = struct.unpack_from('<H', dex, i+2)[0]
            print(f"  {pc:#06x}: invoke {method_at(midx2)}")
            i += 6; pc += 3
        elif opc == 0x22:
            tidx = struct.unpack_from('<H', dex, i+2)[0]
            print(f"  {pc:#06x}: new-instance {type_at(tidx)}")
            i += 4; pc += 2
        elif opc in (0x37,0x38,0x39,0x3a,0x3b,0x3c):
            tgt = struct.unpack_from('<h', dex, i+2)[0]
            print(f"  {pc:#06x}: if-cmp->{tgt:#06x}")
            i += 4; pc += 2
        elif opc in (0x28,):
            tgt = struct.unpack_from('<h', dex, i+1)[0] if False else None
            # packed 10bit
            aa = (unit >> 8) & 0xFF
            if aa == 0x28:  # goto
                off8 = struct.unpack_from('<b', dex, i+1)[0]
                print(f"  {pc:#06x}: goto {pc+off8:#06x}")
                i += 2; pc += 1
            else:
                print(f"  {pc:#06x}: op_{opc:#04x}")
                i += 2; pc += 1
        elif opc == 0x0e:
            print(f"  {pc:#06x}: return-void")
            i += 2; pc += 1
        elif opc in (0x11,):
            print(f"  {pc:#06x}: return-object")
            i += 2; pc += 1
        elif opc in (0x0f,):
            print(f"  {pc:#06x}: return")
            i += 2; pc += 1
        elif opc == 0x26:
            tgt = struct.unpack_from('<i', dex, i+2)[0] if False else None
            print(f"  {pc:#06x}: throw (32-bit)")
            i += 4; pc += 2
        elif opc == 0x0c:
            print(f"  {pc:#06x}: move-result-object")
            i += 2; pc += 1
        elif opc == 0x12:
            b = (unit >> 8) & 0xFF
            print(f"  {pc:#06x}: const/4 v{(unit>>12)&0xF}, {((b<<28)>>28)}")
            i += 2; pc += 1
        else:
            print(f"  {pc:#06x}: op_{opc:#04x} unit={unit:#06x}")
            # conservative advance: guess by high nibble common sizes
            if opc in (0x13,0x16,0x1c,0x1f,0x20,0x23,0x31,0x32,0x33,0x34,0x35,0x36):
                i += 4; pc += 2
            elif opc in (0x14,0x15,0x17,0x19,0x21):
                i += 4; pc += 2
            elif opc == 0x1a:
                i += 4; pc += 2
            else:
                i += 2; pc += 1
        if pc > 420: break
    break
if not found:
    print(f"method '{want_method}' not found in {target}")
