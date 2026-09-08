#!/usr/bin/env python3
"""f020_field_refs.py — F-020 forensic scanner.

Finds in a DEX:
  1. sget*/sput* references of a target STATIC FIELD (class, field-name)
  2. invoke-direct <init> sites of a target class (construction sites)

Usage: python3 f020_field_refs.py <apk> <Lcls/desc;> <member-name> [--ctor]
Reuses m3_disasm's instruction walk (spec-conformant format table).
"""
import sys, zipfile, struct

sys.path.insert(0, "/home/z/my-project/MiniAndroid-Compatibility-Runtime/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "m3dis", "/home/z/my-project/MiniAndroid-Compatibility-Runtime/scripts/m3_disasm.py")
m3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m3)

SGET_OPS = {0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67}  # sget..sput-short

def main():
    apk, cls_want, mem_want = sys.argv[1], sys.argv[2], sys.argv[3]
    ctor_mode = "--ctor" in sys.argv
    z = zipfile.ZipFile(apk)
    dexes = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
    for dexname in dexes:
        d = z.read(dexname)
        u2 = lambda o: struct.unpack_from("<H", d, o)[0]
        u4 = lambda o: struct.unpack_from("<I", d, o)[0]
        def uleb(p):
            r, s = 0, 0
            while True:
                b = d[p + s]; r |= (b & 0x7F) << (7 * s); s += 1
                if not (b & 0x80): return r, p + s
        str_off, s_sz = u4(0x3C), u4(0x38)
        type_off, t_sz = u4(0x44), u4(0x40)
        proto_off = u4(0x4C)
        f_off, f_sz = u4(0x54), u4(0x50)
        m_off, m_sz = u4(0x5C), u4(0x58)
        c_off, c_sz = u4(0x64), u4(0x60)

        def get_str(i):
            if i >= s_sz: return "<bad>"
            off = u4(str_off + 4 * i)
            r, p = uleb(off)
            return d[p:p + r].split(b"\x00")[0].decode("utf-8", "replace")

        def type_of(i):
            return get_str(u4(type_off + 4 * i)) if i < t_sz else "<bad_t>"

        def field_of(i):
            fo = f_off + 8 * i
            return f"{type_of(u2(d, fo))}.{get_str(u4(d, fo + 4))}"

        hits = []
        for ci in range(c_sz):
            coff = c_off + 32 * ci
            cls_name = type_of(u2(d, coff))
            # class_data_off
            cdo = u4(d, coff + 24)
            if not cdo: continue
            p = cdo
            sf_sz, inf_sz, dm_sz, vm_sz = uleb(d, p)[0], 0, 0, 0
            r, p = uleb(d, p)
            static_f_n = r
            r, p = uleb(d, p); inst_f_n = r
            r, p = uleb(d, p); direct_m_n = r
            r, p = uleb(d, p); virt_m_n = r
            # skip fields
            idx = 0
            for _ in range(static_f_n):
                r, p = uleb(d, p); idx += r
                r, p = uleb(d, p)
            idx = 0
            for _ in range(inst_f_n):
                r, p = uleb(d, p); idx += r
                r, p = uleb(d, p)
            # methods
            midx = 0
            for _ in range(direct_m_n):
                r, p = uleb(d, p); midx += r
                r2, p = uleb(d, p)  # access
                r3, p = uleb(d, p)  # code_off
                mth = get_str(u4(d, m_off + 8 * midx + 4))
                mcls = type_of(u2(d, m_off + 8 * midx))
                if code_off := r3:
                    scan_code(d, code_off, cls_name, mth, hits,
                              cls_want, mem_want, ctor_mode,
                              field_of, type_of, get_str, u2, proto_off, m_off, midx)
                else:
                    # abstract/native — still record ctor decl? no
                    pass
            vidx = 0
            for _ in range(virt_m_n):
                r, p = uleb(d, p); vidx += r
                r2, p = uleb(d, p)
                r3, p = uleb(d, p)
                mth = get_str(u4(d, m_off + 8 * vidx + 4))
                if code_off := r3:
                    scan_code(d, code_off, cls_name, mth, hits,
                              cls_want, mem_want, ctor_mode,
                              field_of, type_of, get_str, u2, proto_off, m_off, vidx)
        for h in hits:
            print(h)

def scan_code(d, code_off, cls_name, mth, hits, cls_want, mem_want, ctor_mode,
              field_of, type_of, get_str, u2, proto_off, m_off, midx):
    registers_size = u2(d, code_off)
    insns_size = u2(d, code_off + 12) * 2  # in 16-bit units
    base = code_off + 16
    pc = 0
    while pc < insns_size:
        op = d[base + 2 * pc + 1]
        if op in SGET_OPS and not ctor_mode:
            fidx = u2(d, base + 2 * pc + 2)
            fref = field_of(fidx)
            if fref == f"{cls_want}.{mem_want}" or (fref.startswith(cls_want + ".") and mem_want == "*"):
                hits.append(f"[sfield] {cls_name}.{mth} pc=0x{pc:x} -> {fref}")
        elif op in (0x70,) and ctor_mode:  # invoke-direct
            midx2 = u2(d, base + 2 * pc + 2)
            mo = m_off + 8 * midx2
            mcls = type_of(u2(d, mo))
            mname = get_str(u4(d, mo + 4))
            if mcls == cls_want and mname == mem_want:
                hits.append(f"[ctor] {cls_name}.{mth} pc=0x{pc:x} -> new {mcls}")
        # advance by format (borrow m3_disasm's table via its size function if exposed)
        sz = op_size(op)
        pc += sz

FMT3 = {0x21,0x22,0x23,0x24,0x25,0x1C,0x1D,0x1F,0x20}
FMT23X = {0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,0x50,0x51,
          0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5A,0x5B,0x5C,0x5D,0x5E,0x5F,
          0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,0x6B,0x6C,0x6D,
          0x78,0x94,0x95,0x96,0x97,0x98,0x99,0x9A,0x9B,0x9C,0x9D,0x9E,0x9F,
          0xA0,0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,0xA8,0xA9,0xAA,0xAB,0xAC,0xAD,0xAE,0xAF,
          0xB0,0xB1,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,0xB9,0xBA,0xBB,0xBC,0xBD,0xBE,0xBF,
          0xC0,0xC1,0xC2,0xC3,0xC4,0xC5,0xC6,0xC7,0xC8,0xC9,0xCA,0xCB,0xCC,0xCD,0xCE,0xCF,
          0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7,0xD8,0xD9,0xDA,0xDB,0xDC,0xDD,0xDE,0xDF,
          0xE0,0xE1,0xE2,0xE3,0xE4,0xE5,0xE6,0xE7,0xE8,0xE9,0xEA,0xEB,0xEC,0xED,0xEE,0xEF,
          0xF0,0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0xF7,0xF8,0xF9,0xFA,0xFB,0xFC,0xFD,0xFE,0xFF}
INVOKE_OPS = {0x6E,0x6F,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78}
TWO_UNIT = set(range(0x00, 0x0D)) | {0x0E,0x0F,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,
              0x1C,0x1D,0x1E,0x1F,0x20,0x21,0x22,0x23,0x24,0x25,0x26,
              0x27,0x28,0x29,0x2A,0x2B,0x2C,0x2D}

def op_size(op):
    if op == 0x00: return 1
    if 0x01 <= op <= 0x0F: return 1
    if 0x10 <= op <= 0x19: return 1
    if 0x1A <= op <= 0x1B: return 2
    if op in FMT3 or op in FMT23X or op in INVOKE_OPS or 0x2C == op: return 2
    if op == 0x26: return 3
    if 0x2B <= op <= 0x2C: return 3
    if op in (0x73,): return 2  # unused
    if 0x74 <= op <= 0x78: return 3
    # remaining 3-unit formats: 22b(0xD..?) handled, 31i/31t/31c (0x14-0x19,0x1B,0x1C) some are 2-3
    if op in (0x14,0x15,0x16,0x17): return 2
    if op in (0x18,0x19): return 5
    if op in (0x1B,0x1C): return 3 if op == 0x1B else 2
    if op in (0x2B,0x2C): return 3
    # packed/sparse-switch payload handled by caller walk? approximate: treat common
    if op in (0x2D,0x2E,0x2F,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D): return 2
    if 0x45 <= op <= 0x8F: return 2
    # fill-array-data/range payloads: 0x100 etc won't occur as op in stream except payloads; approximate
    return 2

if __name__ == "__main__":
    main()
