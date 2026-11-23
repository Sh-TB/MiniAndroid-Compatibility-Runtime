#!/usr/bin/env python3
"""S27-W2 forensics: dump EVERY method overload of a class (find_method
returns only the first match; the InitializerViewModelFactory create(Class)
bridge and create(Class, CreationExtras) loop are distinct methods).
Reuses dump_method_bytecode.DexFile for the heavy parsing."""
import sys, zipfile
sys.path.insert(0, '/home/z/my-project/miniandroid/tools')
from dump_method_bytecode import DexFile, OPCODE_NAMES, get_size

APK = sys.argv[1]
CLASS = sys.argv[2]          # e.g. Landroidx/lifecycle/viewmodel/InitializerViewModelFactory;
MNAME = sys.argv[3]          # e.g. create  ('*' = all methods)

def disasm(dex, code_off, label):
    regs = dex._u16(code_off); ins = dex._u16(code_off + 2)
    outs = dex._u16(code_off + 4); insns_size = dex._u32(code_off + 12)
    insns_off = code_off + 16
    print(f"# {label} regs={regs} ins={ins} outs={outs} insns={insns_size}")
    pc = 0
    while pc < insns_size:
        op_off = insns_off + pc * 2
        op = dex.data[op_off] | (dex.data[op_off + 1] << 8)
        op_low = op & 0xFF
        size = get_size(op_low, dex.data, op_off)
        line = f"  PC=0x{pc:04x} ({pc:3d}) {OPCODE_NAMES.get(op_low, f'unk-0x{op_low:02x}')}"
        if op_low in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78) and size >= 2:
            midx = dex._u16(op_off + 2)
            c, n = dex.get_method_descriptor(midx)
            line += f" → {c}.{n} {dex.get_method_shorty(dex._u16(op_off+2)) if False else ''}"
        elif op_low == 0x22 and size >= 2:
            line += f" → {dex.get_type_descriptor(dex._u16(op_off + 2))}"
        elif 0x52 <= op_low <= 0x6d and size >= 2:
            fidx = dex._u16(op_off + 2)
            line += f" field#{fidx} {dex._field_desc(fidx) if hasattr(dex,'_field_desc') else ''}"
        print(line)
        if size == 0:
            print("  # unknown size, break"); break
        pc += size
    print()

for dex_name in sorted(n for n in zipfile.ZipFile(APK).namelist() if n.endswith('.dex')):
    data = zipfile.ZipFile(APK).read(dex_name)
    dex = DexFile(data, dex_name)
    # walk class_defs
    for i in range(dex.class_defs_size):
        cd = dex.class_defs_off + i * 32
        desc_idx = dex._u32(cd)
        if dex.get_type_descriptor(desc_idx) != CLASS:
            continue
        cd_off = dex._u32(cd + 24)
        if cd_off == 0:
            print(f"{dex_name}: {CLASS} has no class_data"); continue
        off = cd_off
        sfc, off = dex._read_uleb128(off)
        ifc, off = dex._read_uleb128(off)
        dm, off = dex._read_uleb128(off)
        vm, off = dex._read_uleb128(off)
        # consume encoded_field entries: (field_idx_diff, access_flags)
        f_idx = 0
        for _ in range(sfc + ifc):
            d, off = dex._read_uleb128(off)
            a, off = dex._read_uleb128(off)
        for kind, count in (("direct", dm), ("virtual", vm)):
            m_idx = 0
            for _ in range(count):
                d, off = dex._read_uleb128(off)
                m_idx += d
                acc, off = dex._read_uleb128(off)
                code_off, off = dex._read_uleb128(off)
                cname, mname = dex.get_method_descriptor(m_idx)
                proto = dex._method_proto_desc(m_idx) if hasattr(dex, '_method_proto_desc') else ""
                if MNAME == '*' or mname == MNAME:
                    print(f"== {dex_name} {cname}.{mname} idx={m_idx} acc=0x{acc:x} code=0x{code_off:x}")
                    if code_off:
                        disasm(dex, code_off, f"{cname}.{mname}")
                else:
                    pass
