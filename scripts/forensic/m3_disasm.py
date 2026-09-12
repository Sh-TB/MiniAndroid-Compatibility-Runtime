#!/usr/bin/env python3
"""
scripts/forensic/m3_disasm.py — readable Dalvik disassembler for MASTER-3 forensics (RULE 2).

Ground-truth app semantics BEFORE any law fix. Walks class_def ->
class_data -> code_item and decodes instructions with pc annotations.
Coverage: the opcode families the interpreter audits touch — const/move/
return, arithmetic (+literal/+wide), comparisons, arrays, fields, invokes
(including range forms), branches (incl. payload-resolved), switches,
fill-array-data, monitor, check-cast/instance-of, new-instance/array.

Usage:
  python3 scripts/forensic/m3_disasm.py <apk> Lk/d; onClick
  python3 scripts/forensic/m3_disasm.py <apk> Lk/d;            # all methods
"""
import struct, zipfile, sys

# ---- opcode tables -------------------------------------------------------
FMT = {}  # op -> (name, fmt-letter)
_CORE = """
00 nop 10x;
01 move 12x;
02 move/from16 22x;
03 move/16 32x;
04 move-wide 12x;
05 move-wide/from16 22x;
06 move-wide/16 32x;
07 move-object 12x;
08 move-object/from16 22x;
09 move-object/16 32x;
0a move-result 11x;
0b move-result-wide 11x;
0c move-result-object 11x;
0d move-exception 11x;
0e return-void 10x;
0f return 11x;
10 return-wide 11x;
11 return-object 11x;
12 const/4 11n;
13 const/16 21s;
14 const 31i;
15 const/high16 21h;
16 const-wide/16 21s;
17 const-wide/32 31i;
18 const-wide 51l;
19 const-wide/high16 21h;
1a const-string 21c;
1b const-string/jumbo 31c;
1c const-class 21c;
1d monitor-enter 11x;
1e monitor-exit 11x;
1f check-cast 21c;
20 instance-of 22c;
21 array-length 12x;
22 new-instance 21c;
23 new-array 22c;
24 filled-new-array 35c;
25 filled-new-array/range 3rc;
26 fill-array-data 31t;
27 throw 11x;
28 goto 10t;
29 goto/16 20t;
2a goto/32 30t;
2b packed-switch 31t;
2c sparse-switch 31t;
2d cmpl-float 23x;
2e cmpg-float 23x;
2f cmpl-double 23x;
30 cmpg-double 23x;
31 cmp-long 23x;
32 if-eq 22t;
33 if-ne 22t;
34 if-lt 22t;
35 if-ge 22t;
36 if-gt 22t;
37 if-le 22t;
38 if-eqz 21t;
39 if-nez 21t;
3a if-ltz 21t;
3b if-gez 21t;
3c if-gtz 21t;
3d if-lez 21t;
44 aget 23x;
45 aget-wide 23x;
46 aget-object 23x;
47 aget-boolean 23x;
48 aget-byte 23x;
49 aget-char 23x;
4a aget-short 23x;
4b aput 23x;
4c aput-wide 23x;
4d aput-object 23x;
4e aput-boolean 23x;
4f aput-byte 23x;
50 aput-char 23x;
51 aput-short 23x;
52 iget 22c;
53 iget-wide 22c;
54 iget-object 22c;
55 iget-boolean 22c;
56 iget-byte 22c;
57 iget-char 22c;
58 iget-short 22c;
59 iput 22c;
5a iput-wide 22c;
5b iput-object 22c;
5c iput-boolean 22c;
5d iput-byte 22c;
5e iput-char 22c;
5f iput-short 22c;
60 sget 21c;
61 sget-wide 21c;
62 sget-object 21c;
63 sget-boolean 21c;
64 sget-byte 21c;
65 sget-char 21c;
66 sget-short 21c;
67 sput 21c;
68 sput-wide 21c;
69 sput-object 21c;
6a sput-boolean 21c;
6b sput-byte 21c;
6c sput-char 21c;
6d sput-short 21c;
6e invoke-virtual 35c;
6f invoke-super 35c;
70 invoke-direct 35c;
71 invoke-static 35c;
72 invoke-interface 35c;
74 invoke-virtual/range 3rc;
75 invoke-super/range 3rc;
76 invoke-direct/range 3rc;
77 invoke-static/range 3rc;
78 invoke-interface/range 3rc;
7b neg-int 12x;
7c not-int 12x;
7d neg-long 12x;
7e not-long 12x;
7f neg-float 12x;
80 neg-double 12x;
81 int-to-long 12x;
82 int-to-float 12x;
83 int-to-double 12x;
84 long-to-int 12x;
85 long-to-float 12x;
86 long-to-double 12x;
87 float-to-int 12x;
88 float-to-long 12x;
89 float-to-double 12x;
8a double-to-int 12x;
8b double-to-long 12x;
8c double-to-float 12x;
8d int-to-byte 12x;
8e int-to-char 12x;
8f int-to-short 12x;
90 add-int 23x;
91 sub-int 23x;
92 mul-int 23x;
93 div-int 23x;
94 rem-int 23x;
95 and-int 23x;
96 or-int 23x;
97 xor-int 23x;
98 shl-int 23x;
99 shr-int 23x;
9a ushr-int 23x;
9b add-long 23x;
9c sub-long 23x;
9d mul-long 23x;
9e div-long 23x;
9f rem-long 23x;
a0 and-long 23x;
a1 or-long 23x;
a2 xor-long 23x;
a3 shl-long 23x;
a4 shr-long 23x;
a5 ushr-long 23x;
a6 add-float 23x;
a7 sub-float 23x;
a8 mul-float 23x;
a9 div-float 23x;
aa rem-float 23x;
ab add-double 23x;
ac sub-double 23x;
ad mul-double 23x;
ae div-double 23x;
af rem-double 23x;
b0 add-int/2addr 12x;
b1 sub-int/2addr 12x;
b2 mul-int/2addr 12x;
b3 div-int/2addr 12x;
b4 rem-int/2addr 12x;
b5 and-int/2addr 12x;
b6 or-int/2addr 12x;
b7 xor-int/2addr 12x;
b8 shl-int/2addr 12x;
b9 shr-int/2addr 12x;
ba ushr-int/2addr 12x;
bb add-long/2addr 12x;
bc sub-long/2addr 12x;
bd mul-long/2addr 12x;
be div-long/2addr 12x;
bf rem-long/2addr 12x;
c0 and-long/2addr 12x;
c1 or-long/2addr 12x;
c2 xor-long/2addr 12x;
c3 shl-long/2addr 12x;
c4 shr-long/2addr 12x;
c5 ushr-long/2addr 12x;
c6 add-float/2addr 12x;
c7 sub-float/2addr 12x;
c8 mul-float/2addr 12x;
c9 div-float/2addr 12x;
ca rem-float/2addr 12x;
cb add-double/2addr 12x;
cc sub-double/2addr 12x;
cd mul-double/2addr 12x;
ce div-double/2addr 12x;
cf rem-double/2addr 12x;
d0 add-int/lit16 22s;
d1 rsub-int 22s;
d2 mul-int/lit16 22s;
d3 div-int/lit16 22s;
d4 rem-int/lit16 22s;
d5 and-int/lit16 22s;
d6 or-int/lit16 22s;
d7 xor-int/lit16 22s;
d8 add-int/lit8 22b;
d9 rsub-int/lit8 22b;
da mul-int/lit8 22b;
db div-int/lit8 22b;
dc rem-int/lit8 22b;
dd and-int/lit8 22b;
de or-int/lit8 22b;
df xor-int/lit8 22b;
e0 shl-int/lit8 22b;
e1 shr-int/lit8 22b;
e2 ushr-int/lit8 22b;
fa invoke-polymorphic 45cc;
fb invoke-polymorphic/range 4rcc;
fc invoke-custom 35c;
fd invoke-custom/range 3rc;
"""
_S = {}
for tok in _CORE.split(";"):
    tok = tok.strip()
    if not tok:
        continue
    parts = tok.split()
    if len(parts) >= 2:
        rng = parts[0].split("-")
        if len(rng) == 2:  # e.g. "3e-43 unused-3e-43" — reserved span
            lo, hi2 = int(rng[0], 16), int(rng[1], 16)
            for o in range(lo, hi2 + 1):
                _S[o] = (parts[1], parts[2])
            continue
        op = int(parts[0], 16)
        _S[op] = (parts[1], parts[2])

SIZES = {"10x": 1, "12x": 1, "11n": 1, "11x": 1, "10t": 1,
         "20t": 2, "22x": 2, "21s": 2, "21h": 2, "21c": 2, "23x": 2, "22b": 2,
         "22t": 2, "22s": 2, "22c": 2, "21t": 2, "32x": 2,
         "30t": 3, "31i": 3, "31t": 3, "31c": 3,
         "51l": 5, "35c": 3, "3rc": 3, "45cc": 4, "4rcc": 4}


def u1(d, o): return d[o]
def u2(d, o): return struct.unpack_from("<H", d, o)[0]
def u4(d, o): return struct.unpack_from("<I", d, o)[0]
def s2(d, o): return struct.unpack_from("<h", d, o)[0]
def s4(d, o): return struct.unpack_from("<i", d, o)[0]
def s8(d, o): return struct.unpack_from("<q", d, o)[0]


def uleb(d, p):
    r = 0; s = 0
    while True:
        b = u1(d, p + s); r |= (b & 0x7f) << (7 * s); s += 1
        if not (b & 0x80):
            return r, p + s


def decode_word(w):
    return w & 0xff, (w >> 8) & 0xff


def reglist(d, pc, count, start):
    return ", ".join(f"v{u2(d, pc + 4 + 2 * (i))}" for i in range(count))


def disasm(d, strtab, type_of, field_of, meth_of, code_off, insns_size):
    """Yield (pc, text) decoded lines. code_off points at insns start."""
    pc = 0
    out = []
    end = insns_size  # in 16-bit code units
    while pc < end:
        w = u2(d, code_off + 2 * pc)
        op, hi = decode_word(w)
        # Pseudo-payloads (dex-format#packed-switch-payload etc.) — consume
        # their full size so the instruction stream stays aligned.
        if op == 0x00 and hi == 0x01:  # packed-switch-payload
            size = u2(d, code_off + 2 * pc + 2)
            sz = size * 2 + 4
            out.append((pc, f"<packed-switch-payload size={size}>"))
            pc += sz
            continue
        if op == 0x00 and hi == 0x02:  # sparse-switch-payload
            size = u2(d, code_off + 2 * pc + 2)
            sz = size * 4 + 2
            out.append((pc, f"<sparse-switch-payload size={size}>"))
            pc += sz
            continue
        if op == 0x00 and hi == 0x03:  # fill-array-data-payload
            width = u2(d, code_off + 2 * pc + 2)
            count = u4(d, code_off + 2 * pc + 4)
            sz = 4 + (width * count + 1) // 2
            out.append((pc, f"<fill-array-data-payload width={width} count={count}>"))
            pc += sz
            continue
        name, fmt = _S.get(op, ("<op-%02x>" % op, "10x"))
        sz = SIZES.get(fmt, 1)
        try:
            txt = _fmt_text(d, code_off, pc, w, op, hi, name, fmt,
                            strtab, type_of, field_of, meth_of)
        except Exception as e:  # noqa: BLE001 — disassembler must not die
            txt = f"<decode-error {e}>"
        out.append((pc, txt))
        pc += sz
    return out


def _sgn16(v):
    return v - 0x10000 if v >= 0x8000 else v


def _sgn8(v):
    return v - 0x100 if v >= 0x80 else v


def _fmt_text(d, base, pc, w, op, hi, name, fmt, strtab, type_of, field_of, meth_of):
    """Decode per Dalvik executable instruction formats (dex-format#formats)."""
    A = (w >> 8) & 0xf
    AA = (w >> 8) & 0xff
    if fmt == "10x":
        return name
    if fmt == "12x":
        return f"{name} v{(w >> 12) & 0xf}, v{A}"
    if fmt == "11n":
        lit = (w >> 12) & 0xf
        lit = lit - 16 if lit >= 8 else lit
        return f"{name} v{A}, #{lit}"
    if fmt == "11x":
        return f"{name} v{AA}"
    if fmt == "10t":
        return f"{name} -> {pc + _sgn8(AA):#x}"
    if fmt == "20t":
        return f"{name} -> {pc + _sgn16(u2(d, base + 2 * pc + 2)):#x}"
    if fmt == "21t":
        return f"{name} v{AA}, -> {pc + _sgn16(u2(d, base + 2 * pc + 2)):#x}"
    if fmt == "32x":
        u1v = u2(d, base + 2 * pc + 2)
        return f"{name} v{u1v & 0xffff}, v{u2(d, base + 2 * pc + 4)}"
    if fmt == "22x":
        return f"{name} v{AA}, v{u2(d, base + 2 * pc + 2)}"
    if fmt == "21s":
        return f"{name} v{AA}, #{_sgn16(u2(d, base + 2 * pc + 2))}"
    if fmt == "21h":
        v = _sgn16(u2(d, base + 2 * pc + 2))
        v = v << 48 if op == 0x19 else v << 16
        return f"{name} v{AA}, #{v:#x}"
    if fmt == "21c":
        idx = u2(d, base + 2 * pc + 2)
        if op in (0x1a, 0x1b):
            return f'{name} v{AA}, "{strtab(idx)}"'
        return f"{name} v{AA}, {type_of(idx) if op == 0x1c else (field_of(idx) if op >= 0x60 else type_of(idx))}"
    if fmt == "23x":
        u1v = u2(d, base + 2 * pc + 2)
        return f"{name} v{AA}, v{u1v & 0xff}, v{u1v >> 8}"
    if fmt == "22b":
        # 22b diagram: AA|op, CC|BB — BB is the LOW byte (register),
        # CC the HIGH byte (signed literal). d805 05ff -> v5, v5, #-1.
        u1v = u2(d, base + 2 * pc + 2)
        return f"{name} v{AA}, v{u1v & 0xff}, #{_sgn8((u1v >> 8) & 0xff)}"
    if fmt in ("22t", "22s", "22c"):
        # 22x diagrams are B|A|op: A = low nibble of the high byte (first
        # reg, the DESTINATION for 22c/22s), B = top nibble (second reg).
        Areg = (w >> 8) & 0xf
        Breg = (w >> 12) & 0xf
        u2v = _sgn16(u2(d, base + 2 * pc + 2))
        if fmt == "22t":
            return f"{name} v{Areg}, v{Breg} -> {pc + u2v:#x}"
        if fmt == "22s":
            return f"{name} v{Areg}, v{Breg}, #{u2v}"
        idx = u2(d, base + 2 * pc + 2)
        what = field_of(idx) if op >= 0x52 else type_of(idx)
        return f"{name} v{Areg}, v{Breg}, {what}"
    if fmt == "30t":
        return f"{name} -> {pc + s4(d, base + 2 * pc + 2):#x}"
    if fmt == "31i":
        return f"{name} v{AA}, #{s4(d, base + 2 * pc + 2):#x}"
    if fmt == "31t":
        off = s4(d, base + 2 * pc + 2)
        return f"{name} v{AA}, -> payload@{pc + off:#x}"
    if fmt == "31c":
        idx = u4(d, base + 2 * pc + 2)
        return f'{name} v{AA}, "{strtab(idx)}"'
    if fmt == "51l":
        return f"{name} v{AA}, #{s8(d, base + 2 * pc + 2):#x}"
    if fmt == "35c":
        # AOSP instruction-formats law: 35c = A|G|op, BBBB, F|E|D|C.
        # The REFERENCE INDEX is the SECOND unit; registers are the THIRD
        # ("same label as in format 3rc" — verified against the live spec,
        # androguard, and the runtime's own resolution).
        idx = u2(d, base + 2 * pc + 2)
        FEDC = u2(d, base + 2 * pc + 4)
        cnt = (w >> 12) & 0xf
        G = A
        C, D, E, F = FEDC & 0xf, (FEDC >> 4) & 0xf, (FEDC >> 8) & 0xf, (FEDC >> 12) & 0xf
        vals = [C, D, E, F, G][:cnt]
        return f"{name} {{ {', '.join('v'+str(v) for v in vals)} }}, {meth_of(idx)}"
    if fmt == "3rc":
        # 3rc: AA|op, CCCC, BBBB — start reg is the SECOND unit, index third.
        first = u2(d, base + 2 * pc + 2)
        idx = u2(d, base + 2 * pc + 4)
        cnt = AA
        return f"{name} {{ v{first}..v{first + cnt - 1} }}, {meth_of(idx)}"
    return name


def main():
    apk, cls_want = sys.argv[1], sys.argv[2]
    meth_want = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(apk)
    d = z.read("classes.dex")
    # DEX header map (AOSP DexHeader): string_ids_size=0x38 off=0x3C;
    # type 0x40/0x44; proto 0x48/0x4C; field 0x50/0x54; method 0x58/0x5C;
    # class_defs 0x60/0x64. (Verified against hexdump of microtimer classes.dex.)
    str_off, s_sz = u4(d, 0x3C), u4(d, 0x38)
    type_off, t_sz = u4(d, 0x44), u4(d, 0x40)
    proto_off = u4(d, 0x4C)
    f_off = u4(d, 0x54)
    m_off, m_sz = u4(d, 0x5C), u4(d, 0x58)
    c_off, c_sz = u4(d, 0x64), u4(d, 0x60)

    def get_str(idx):
        if idx >= s_sz:
            return "<bad_str>"
        off = u4(d, str_off + 4 * idx)
        r, p = uleb(d, off)
        return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

    def type_of(idx):
        if idx >= t_sz:
            return "<bad_type>"
        return get_str(u4(d, type_off + 4 * idx))

    def field_of(idx):
        fo = f_off + 8 * idx  # field_id: class u2, type u2, name u4
        return f"{type_of(u2(d, fo))}.{get_str(u4(d, fo + 4))}"

    def meth_of(idx):
        mo = m_off + 8 * idx  # method_id: class u2, proto u2, name u4
        cls = type_of(u2(d, mo))
        name = get_str(u4(d, mo + 4))
        # proto: shorty + return + params (proto_id = 12 bytes)
        po = proto_off + 12 * u2(d, mo + 2)
        ret = type_of(u2(d, po + 4))
        params_off = u4(d, po + 8)
        params = []
        if params_off:
            n = u4(d, params_off)
            for k in range(n):
                params.append(type_of(u2(d, params_off + 4 + 2 * k)))
        return f"{cls}.{name}({', '.join(params)}){ret}"

    def print_method(tn2, name2, d32):
        regs = u2(d, d32); ins = u2(d, d32 + 2)
        outs = u2(d, d32 + 4)
        isz = u4(d, d32 + 12)
        code = d32 + 16
        print(f"\n=== {tn2}.{name2} regs={regs} ins={ins} outs={outs} words={isz} ===")
        for pc, txt in disasm(d, get_str, type_of, field_of, meth_of,
                              code, isz):
            print(f"  {pc:#06x}: {txt}")

    for i in range(c_sz):
        off = c_off + 32 * i
        tn = type_of(u4(d, off))
        if cls_want and tn != cls_want:
            continue
        cdo = u4(d, off + 24)
        if not cdo:
            continue
        p = cdo
        sf, p = uleb(d, p); iff, p = uleb(d, p)
        dm, p = uleb(d, p); vm, p = uleb(d, p)
        for _ in range(sf + iff):
            _, p = uleb(d, p); _, p = uleb(d, p)
        # DEX spec (dex-format#encoded-method): the method_idx delta chain
        # RESETS for each sub-list ("the very first element in a list is
        # represented directly"). Same law as the runtime parser
        # (dex_parser.cpp: method_idx=0 before dm and vm loops).
        midx = 0
        for _ in range(dm):
            d1, p = uleb(d, p); d2, p = uleb(d, p); d3, p = uleb(d, p)
            midx += d1  # accumulate WITHIN the list; reset between lists
            if midx >= m_sz or not d3:
                continue
            name = get_str(u4(d, m_off + 8 * midx + 4))
            if meth_want and name != meth_want:
                continue
            print_method(tn, name, d3)
        midx = 0  # virtual_methods: independent chain (DEX spec)
        for _ in range(vm):
            d1, p = uleb(d, p); d2, p = uleb(d, p); d3, p = uleb(d, p)
            midx += d1
            if midx >= m_sz or not d3:
                continue
            name = get_str(u4(d, m_off + 8 * midx + 4))
            if meth_want and name != meth_want:
                continue
            print_method(tn, name, d3)


if __name__ == "__main__":
    main()
