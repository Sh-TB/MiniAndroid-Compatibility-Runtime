#!/usr/bin/env python3
"""cont7w2_find_string_xref.py — find which class/method in a DEX references a
given string (const-string xref) and dump surrounding bytecode.
Usage: cont7w2_find_string_xref.py <apk_or_dex> <substring> [class_filter]
F-NEW-252 WAVE-2: locate the thrower of "Only add dependencies during a
tracking block" in dooz classes.dex (app-bundled R8-renamed Compose runtime).
"""
import sys, zipfile, struct

APK = sys.argv[1]
NEEDLE = sys.argv[2]
CLSFILTER = sys.argv[3] if len(sys.argv) > 3 else None

if APK.endswith('.dex'):
    b = open(APK, 'rb').read()
else:
    z = zipfile.ZipFile(APK)
    b = z.read('classes.dex')

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
    return get_type(cls), get_string(name)

def get_field(i):
    cls, typ, name = struct.unpack_from('<HHI', b, field_ids_off + i*8)
    return get_type(cls), get_string(name)

# 1. find string index(es)
targets = []
for i in range(string_ids_size):
    try:
        s = get_string(i)
    except Exception:
        continue
    if NEEDLE in s:
        targets.append((i, s))
print(f"string matches: {[(i, repr(s)[:80]) for i, s in targets]}")
if not targets:
    sys.exit(1)
tset = set(i for i, _ in targets)

# 2. walk class defs -> class_data -> direct/virtual methods -> code_item
def parse_class_data(off):
    sf, off = uleb(off); inf, off = uleb(off)
    dm, off = uleb(off); vm, off = uleb(off)
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

OPCODE_NAMES = {
    0x1a: ('const-string', 2), 0x1b: ('const-string/jumbo', 3),
    0x6e: ('invoke-virtual', 3), 0x6f: ('invoke-super', 3),
    0x70: ('invoke-direct', 3), 0x71: ('invoke-static', 3),
    0x72: ('invoke-interface', 3), 0x74: ('invoke-virtual/range', 3),
    0x76: ('invoke-direct/range', 3), 0x77: ('invoke-static/range', 3),
    0x78: ('invoke-interface/range', 3),
    0x52: ('iget', 2), 0x54: ('iget-object', 2), 0x59: ('iput', 2),
    0x5b: ('iput-object', 2), 0x60: ('sget', 2), 0x62: ('sget-object', 2),
    0x67: ('sput', 2), 0x69: ('sput-object', 2),
    0x22: ('new-instance', 2), 0x23: ('new-array', 2), 0x21: ('array-length', 1),
    0x0e: ('return-void', 1), 0x0f: ('return', 1), 0x11: ('return-object', 1),
    0x00: ('nop', 1),
}

def decode_method(coff, depth_limit=600):
    """decode a code_item, return list of (pc, text)"""
    if coff == 0:
        return None
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', b, coff)
    insns_off = coff + 16
    out = []
    pc = 0
    while pc < insns_size:
        u0, = struct.unpack_from('<H', b, insns_off + pc*2)
        op = u0 & 0xff
        if op in (0x1a, 0x1b):
            if op == 0x1a:
                reg = u0 >> 8
                idx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            else:
                reg, = struct.unpack_from('<H', b, insns_off + pc*2 + 2)
                idx, = struct.unpack_from('<I', b, insns_off + (pc+1)*2)
            txt = f"const-string v{reg}, idx={idx}"
            if idx in tset:
                txt += f"  <<<< {get_string(idx)[:60]!r}"
            out.append((pc, txt))
            pc += 2 if op == 0x1a else 3
            continue
        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            midx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cls, name = get_method(midx)
            sz = (u0 >> 12) & 0xf
            out.append((pc, f"{OPCODE_NAMES[op][0]} {{v..}} L{cls};.{name} (idx={midx})" if not cls.startswith('L') else f"{OPCODE_NAMES[op][0]} {{v..}} {cls}.{name}"))
            pc += 3
            continue
        if op in (0x74, 0x75, 0x76, 0x77, 0x78):
            midx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cls, name = get_method(midx)
            out.append((pc, f"{OPCODE_NAMES[op][0]} {{v..}} {cls}.{name}"))
            pc += 3
            continue
        if op in (0x52, 0x54, 0x59, 0x5b):
            fidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cls, name = get_field(fidx)
            out.append((pc, f"{OPCODE_NAMES[op][0]} {cls}.{name}"))
            pc += 2
            continue
        if op in (0x60, 0x62, 0x67, 0x69):
            fidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            cls, name = get_field(fidx)
            out.append((pc, f"{OPCODE_NAMES[op][0]} {cls}.{name}"))
            pc += 2
            continue
        if op == 0x22:
            tidx, = struct.unpack_from('<H', b, insns_off + (pc+1)*2)
            out.append((pc, f"new-instance {get_type(tidx)}"))
            pc += 2
            continue
        if op == 0x00 and (u0 >> 8) == 0x00:
            pc += 1
            continue
        # packed/sparse switch payload or unknown: count as 1 unit heuristic
        if op in (0x2c, 0x2b):  # sparse/packed-switch
            out.append((pc, OPCODE_NAMES.get(op, ('switch', 0))[0]))
            pc += 3
            continue
        # generic: try to skip by opcode table for common 2-unit ops
        out.append((pc, f"op {op:#04x} (u0={u0:#06x})"))
        pc += 1
        if len(out) > depth_limit:
            out.append((-1, "... truncated"))
            break
    return out

hits = 0
for ci in range(class_defs_size):
    off = class_defs_off + ci*32
    cls_idx, access, superclass, interfaces_off, src, ann, class_data, sv = struct.unpack_from('<8I', b, off)
    cls = get_type(cls_idx)
    if CLSFILTER and CLSFILTER not in cls:
        continue
    if class_data == 0:
        continue
    for kind, midx, acc, coff in parse_class_data(class_data):
        code = None
        if coff:
            try:
                code = decode_method(coff)
            except Exception as e:
                code = None
        if not code:
            continue
        has_hit = any(pc >= 0 and ('<<<<' in t) for pc, t in code)
        if has_hit:
            hits += 1
            print(f"\n===== {cls} {kind} .{get_method(midx)[1]} (access={acc:#x}, code_off={coff}) =====")
            try:
                mn = get_method(midx)
                print(f"  full: {mn[0]}.{mn[1]}")
            except Exception:
                pass
            for pc, t in code:
                if pc < 0:
                    print(f"    {t}")
                else:
                    mark = '>>' if '<<<<' in t else '  '
                    print(f"  {mark} pc={pc}: {t}")

print(f"\nTOTAL methods referencing string: {hits}")
