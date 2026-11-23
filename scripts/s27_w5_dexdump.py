#!/usr/bin/env python3
"""s27_w5_dexdump.py — minimal read-only DEX method locator/decoder.
Dumps the bytecode of one method (class + method name) from classes.dex
inside the pz APK, with method-ref resolution for invoke-* ops.
Run with: python3 -I s27_w5_dexdump.py <apk> <class-desc> <method>
"""
import struct
import sys
import zipfile

APK = "/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk"
CLS = sys.argv[1] if len(sys.argv) > 1 else "Lname/livitski/games/puzzle/android/model/Board;"
METH = sys.argv[2] if len(sys.argv) > 2 else "placeTilesRandom"

NAMES = {
    0x00: "nop", 0x01: "move", 0x02: "move/from16", 0x03: "move/16",
    0x04: "move-wide", 0x05: "move-wide/from16", 0x06: "move-wide/16",
    0x07: "move-object", 0x08: "move-object/from16", 0x09: "move-object/16",
    0x0a: "move-result", 0x0b: "move-result-wide", 0x0c: "move-result-object",
    0x0d: "move-exception", 0x0e: "return-void", 0x0f: "return",
    0x10: "return-wide", 0x11: "return-object", 0x12: "const/4",
    0x13: "const/16", 0x14: "const", 0x15: "const/high16",
    0x16: "const-wide/16", 0x17: "const-wide/32", 0x18: "const-wide",
    0x19: "const-wide/high16", 0x1a: "const-string", 0x1b: "const-string/jumbo",
    0x1c: "const-class", 0x1d: "monitor-enter", 0x1e: "monitor-exit",
    0x1f: "check-cast", 0x20: "instance-of", 0x21: "array-length",
    0x22: "new-instance", 0x23: "new-array", 0x24: "filled-new-array",
    0x25: "filled-new-array/range", 0x26: "fill-array-data", 0x27: "throw",
    0x28: "goto", 0x29: "goto/16", 0x2a: "goto/32", 0x2b: "packed-switch",
    0x2c: "sparse-switch", 0x2d: "cmpl-float", 0x2e: "cmpg-float",
    0x2f: "cmpl-double", 0x30: "cmpg-double", 0x31: "cmp-long",
    0x32: "if-eq", 0x33: "if-ne", 0x34: "if-lt", 0x35: "if-ge",
    0x36: "if-gt", 0x37: "if-le", 0x38: "if-eqz", 0x39: "if-nez",
    0x3a: "if-ltz", 0x3b: "if-gez", 0x3c: "if-gtz", 0x3d: "if-lez",
    0x3e: "unused-3e", 0x3f: "unused-3f", 0x40: "unused-40",
    0x41: "aget", 0x42: "aget-wide", 0x43: "aget-object", 0x44: "aget-boolean",
    0x45: "aget-byte", 0x46: "aget-char", 0x47: "aget-short",
    0x48: "aput", 0x49: "aput-wide", 0x4a: "aput-object", 0x4b: "aput-boolean",
    0x4c: "aput-byte", 0x4d: "aput-char", 0x4e: "aput-short",
    0x4f: "iget", 0x50: "iget-wide", 0x51: "iget-object", 0x52: "iget-boolean",
    0x53: "iget-byte", 0x54: "iget-char", 0x55: "iget-short",
    0x56: "iput", 0x57: "iput-wide", 0x58: "iput-object", 0x59: "iput-boolean",
    0x5a: "iput-byte", 0x5b: "iput-char", 0x5c: "iput-short",
    0x5d: "sget", 0x5e: "sget-wide", 0x5f: "sget-object", 0x60: "sget-boolean",
    0x61: "sget-byte", 0x62: "sget-char", 0x63: "sget-short",
    0x64: "sput", 0x65: "sput-wide", 0x66: "sput-object", 0x67: "sput-boolean",
    0x68: "sput-byte", 0x69: "sput-char", 0x6a: "sput-short",
    0x6b: "unused-6b", 0x6c: "unused-6c", 0x6d: "unused-6d",
    0x6e: "invoke-virtual", 0x6f: "invoke-super", 0x70: "invoke-direct",
    0x71: "invoke-static", 0x72: "invoke-interface", 0x73: "unused-73",
    0x74: "invoke-virtual/range", 0x75: "invoke-super/range",
    0x76: "invoke-direct/range", 0x77: "invoke-static/range",
    0x78: "invoke-interface/range", 0x79: "unused-79", 0x7a: "unused-7a",
    0x7b: "neg-int", 0x7c: "not-int", 0x7d: "neg-long", 0x7e: "not-long",
    0x7f: "neg-float", 0x80: "neg-double", 0x81: "int-to-long",
    0x82: "int-to-float", 0x83: "int-to-double", 0x84: "long-to-int",
    0x85: "long-to-float", 0x86: "long-to-double", 0x87: "float-to-int",
    0x88: "float-to-long", 0x89: "float-to-double", 0x8a: "double-to-int",
    0x8b: "double-to-long", 0x8c: "double-to-float", 0x8d: "int-to-byte",
    0x8e: "int-to-char", 0x8f: "int-to-short", 0x90: "add-int",
    0x91: "sub-int", 0x92: "mul-int", 0x93: "div-int", 0x94: "rem-int",
    0x95: "and-int", 0x96: "or-int", 0x97: "xor-int", 0x98: "shl-int",
    0x99: "shr-int", 0x9a: "ushr-int", 0x9b: "add-long", 0x9c: "sub-long",
    0x9d: "mul-long", 0x9e: "div-long", 0x9f: "rem-long", 0xa0: "and-long",
    0xa1: "or-long", 0xa2: "xor-long", 0xa3: "shl-long", 0xa4: "shr-long",
    0xa5: "ushr-long", 0xa6: "add-float", 0xa7: "sub-float",
    0xa8: "mul-float", 0xa9: "div-float", 0xaa: "rem-float",
    0xab: "add-double", 0xac: "sub-double", 0xad: "mul-double",
    0xae: "div-double", 0xaf: "rem-double", 0xb0: "add-int/2addr",
    0xb1: "sub-int/2addr", 0xb2: "mul-int/2addr", 0xb3: "div-int/2addr",
    0xb4: "rem-int/2addr", 0xb5: "and-int/2addr", 0xb6: "or-int/2addr",
    0xb7: "xor-int/2addr", 0xb8: "shl-int/2addr", 0xb9: "shr-int/2addr",
    0xba: "ushr-int/2addr", 0xbb: "add-long/2addr", 0xbc: "sub-long/2addr",
    0xbd: "mul-long/2addr", 0xbe: "div-long/2addr", 0xbf: "rem-long/2addr",
    0xc0: "and-long/2addr", 0xc1: "or-long/2addr", 0xc2: "xor-long/2addr",
    0xc3: "shl-long/2addr", 0xc4: "shr-long/2addr", 0xc5: "ushr-long/2addr",
    0xc6: "add-float/2addr", 0xc7: "sub-float/2addr", 0xc8: "mul-float/2addr",
    0xc9: "div-float/2addr", 0xca: "rem-float/2addr", 0xcb: "add-double/2addr",
    0xcc: "sub-double/2addr", 0xcd: "mul-double/2addr", 0xce: "div-double/2addr",
    0xcf: "rem-double/2addr", 0xd0: "add-int/lit16", 0xd1: "rsub-int",
    0xd2: "mul-int/lit16", 0xd3: "div-int/lit16", 0xd4: "rem-int/lit16",
    0xd5: "and-int/lit16", 0xd6: "or-int/lit16", 0xd7: "xor-int/lit16",
    0xd8: "add-int/lit8", 0xd9: "rsub-int/lit8", 0xda: "mul-int/lit8",
    0xdb: "div-int/lit8", 0xdc: "rem-int/lit8", 0xdd: "and-int/lit8",
    0xde: "or-int/lit8", 0xdf: "xor-int/lit8", 0xe0: "shl-int/lit8",
    0xe1: "shr-int/lit8", 0xe2: "ushr-int/lit8",
}

data = zipfile.ZipFile(APK).read("classes.dex")


def u32(off):
    return struct.unpack_from("<I", data, off)[0]


def u16(off):
    return struct.unpack_from("<H", data, off)[0]


def uleb(off):
    r = 0
    s = 0
    while True:
        b = data[off]
        off += 1
        r |= (b & 0x7F) << s
        if not (b & 0x80):
            break
        s += 7
    return r, off


def sleb(off):
    r = 0
    s = 0
    while True:
        b = data[off]
        off += 1
        r |= (b & 0x7F) << s
        s += 7
        if not (b & 0x80):
            if s < 64 and (b & 0x40):
                r -= 1 << s
            break
    return r, off


def cstr(idx):
    str_off = u32(0x3C)  # string_ids_off (the table base VALUE)
    off = u32(str_off + 4 * idx)
    n, off = uleb(off)
    return data[off:off + n].decode("utf-8", "replace")


str_n = u32(0x38)
type_n = u32(0x40)
type_off = u32(0x44)
proto_off = u32(0x4c)
meth_n = u32(0x58)
meth_off = u32(0x5c)
cls_n = u32(0x60)
cls_off = u32(0x64)


def type_str(idx):
    return cstr(u32(type_off + 4 * idx))


def meth_ref(idx):
    mid = meth_off + 8 * idx
    f = u16(mid)      # class_idx
    # proto_idx at +2; name_idx is a U32 at +4
    nm = u32(mid + 4)
    return type_str(f) + "." + cstr(nm)


target_code = None
found_sig = ""
for i in range(cls_n):
    co = cls_off + 32 * i
    if type_str(u32(co)) != CLS:
        continue
    cdo = u32(co + 24)
    if not cdo:
        break
    off = cdo
    sf, off = uleb(off)
    inf, off = uleb(off)
    dm, off = uleb(off)
    vm, off = uleb(off)
    for j in range(sf):
        _, off = uleb(off)  # field_idx_diff
        _, off = uleb(off)  # access_flags
    for j in range(inf):
        _, off = uleb(off)  # field_idx_diff
        _, off = uleb(off)  # access_flags
    idx = 0
    for grp, cnt in (("direct", dm), ("virtual", vm)):
        for k in range(cnt):
            d, off = uleb(off)
            idx += d
            af, off = uleb(off)
            codeoff, off = uleb(off)
            ref = meth_ref(idx)
            base = ref.split("(")[0]
            if base.endswith("." + METH):
                target_code = codeoff
                found_sig = ref
                print("FOUND", grp, ref, "code_off=", hex(codeoff))
    break

if not target_code:
    print("method not found")
    sys.exit(1)

off = target_code
regs = u16(off)
ins = u16(off + 2)
outs = u16(off + 4)
tries = u16(off + 6)
insns_n = u32(off + 12)
insns = off + 16
print("registers=%d ins=%d outs=%d insns_units=%d" % (regs, ins, outs, insns_n))

pc = 0
units = [u16(insns + 2 * i) for i in range(insns_n)]
while pc < insns_n:
    w = units[pc]
    op = w & 0xFF
    name = NAMES.get(op, "op-0x%02x" % op)
    line = "%4d: %-24s" % (pc, name)
    aa = (w >> 8) & 0xFF
    if op in (0x12,):  # const/4 vA, #+B
        line += " v%d, #%d" % (aa, (w >> 12) & 0xF)
    elif op in (0x13, 0x1a, 0x1c, 0x1f, 0x22, 0x5d, 0x5f, 0x60):  # 16-bit idx
        line += " v%d, @%d" % (aa, units[pc + 1])
        if op == 0x1a:
            line += " (%r)" % cstr(units[pc + 1])[:48]
        elif op == 0x22:
            line += " (%s)" % type_str(units[pc + 1])[:52]
    elif op == 0x14:
        imm = struct.unpack_from("<i", data, insns + 2 * pc + 2)[0]
        line += " v%d, #%d" % (aa, imm)
        pc += 1
    elif op in (0x0f, 0x10, 0x11, 0x27, 0x21):
        line += " v%d" % aa
    elif 0x32 <= op <= 0x37:  # if-vN with target
        line += " v%d, v%d -> %+d" % (aa, (w >> 12) & 0xF,
                                      struct.unpack_from("<h", struct.pack("<H", w & 0xFF00 | units[pc + 1] & 0xFF), 0)[0] if False else 0)
        tgt = ((w & 0xFF00) >> 4) | 0  # high byte AA? formats differ; use raw
        # if-vN: AA=regs byte, +BBBB in next unit? Actually AA|BB in first unit
        tgt = (w >> 8) if False else 0
        # simpler: decode signed 16 at pc+... skip precision here
        line = "%4d: %-24s (branch)" % (pc, name)
    elif 0x38 <= op <= 0x3d:  # if-**z +AA (branch in high bits of w)
        off8 = (w >> 8)
        if off8 >= 0x80:
            off8 -= 0x100
        line += " v? -> %+d (target %d)" % (off8, pc + off8)
    elif 0x6e <= op <= 0x72 or 0x74 <= op <= 0x78:
        midx = units[pc + 1]
        line += " @%d %s" % (midx, meth_ref(midx)[:96])
        if op <= 0x72:
            gs = (w >> 12) & 0xF
            regs_l = [(w >> 8) & 0xF]
            if gs:
                more = []
                for g in range(gs):
                    more.append("v%d" % (units[pc + 2] >> (4 * g) & 0xF))
                line += " (" + ",".join(more) + ")"
    elif op in (0x41, 0x42, 0x43, 0x44, 0x48, 0x49, 0x4a):
        line += " v%d v%d v%d" % (aa, (w >> 12) & 0xF, (w >> 8) & 0xF)
    elif op in (0x4f, 0x50, 0x51, 0x56, 0x58):
        line += " v%d f@%d" % (aa, units[pc + 1] >> 0 & 0xFFFF)
    elif op == 0x28:
        off8 = aa
        if off8 >= 0x80:
            off8 -= 0x100
        line += " -> %+d (target %d)" % (off8, pc + off8)
    else:
        line += " w=0x%04x" % w
    print(line)
    # advance by instruction width in 16-bit units (approx: 1 for 1-unit,
    # 2 for most two-unit forms, 3 for const, 5 for goto/32 etc.)
    if op in (0x00, 0x01, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x12, 0x1d,
              0x1e, 0x27, 0x28, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x80) or \
        (0x2d <= op <= 0x31) or (0x32 <= op <= 0x3d) or (0xb0 <= op <= 0xcf):
        pass  # handled per-case below
    width = 1
    if op in (0x02, 0x05, 0x08, 0x13, 0x16, 0x1a, 0x1b and 0, 0x1c, 0x1f,
              0x20, 0x22, 0x23, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47,
              0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x29) or \
        (0x4f <= op <= 0x6a) or (0x6e <= op <= 0x72) or \
        (0x74 <= op <= 0x78) or (0x90 <= op <= 0xaf) or \
        (0xd0 <= op <= 0xd7):
        width = 2
    elif op == 0x14:
        width = 2
    elif op in (0x17, 0x2a):
        width = 3
    elif op == 0x18:
        width = 5
    elif op in (0x24, 0x25, 0x2b, 0x2c, 0x26):
        width = 3
    pc += width
