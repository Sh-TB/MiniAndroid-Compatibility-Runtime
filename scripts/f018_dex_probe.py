#!/usr/bin/env python3
"""F-018 DEX ground-truth probe: list every invoke target reachable from
MainActivity.b (and the alarm-registration block) of microtimer.

Bounded, read-only, diagnostic (ROADMAP §24: bounded/env-safe/repeatable).
Answers: what does the app call AFTER PendingIntent.getBroadcast — i.e.
what is the NEXT demand after the PI fix (AlarmManager family?).
"""
import struct
import sys
import zipfile

def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def uleb128(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, o

def read_dex(dex):
    # header
    string_ids_size = u32(dex, 0x38); string_ids_off = u32(dex, 0x3c)
    type_ids_size = u32(dex, 0x40);  type_ids_off = u32(dex, 0x44)
    proto_ids_off = u32(dex, 0x4c)
    field_ids_size = u32(dex, 0x50); field_ids_off = u32(dex, 0x54)
    method_ids_size = u32(dex, 0x58); method_ids_off = u32(dex, 0x5c)

    def get_string(idx):
        off = u32(dex, string_ids_off + idx * 4)
        # uleb128 length then MUTF-8 bytes
        n, o = uleb128(dex, off)
        end = dex.index(b'\x00', o)
        return dex[o:end].decode('utf-8', 'replace')

    def get_type(idx):
        sidx = u32(dex, type_ids_off + idx * 4)
        return get_string(sidx)

    methods = []
    for i in range(method_ids_size):
        o = method_ids_off + i * 8
        cls_idx = u16(dex, o); proto_idx = u16(dex, o + 2)
        name_idx = u32(dex, o + 4)
        methods.append((get_type(cls_idx), get_string(name_idx), proto_idx))
    return methods, (class_defs_size := None) or u32(dex, 0x60), u32(dex, 0x64), get_type, get_string, u16, u32, dex

def find_method_code(dex, want_cls, want_name):
    class_defs_size = u32(dex, 0x60); class_defs_off = u32(dex, 0x64)
    results = []
    for ci in range(class_defs_size):
        o = class_defs_off + ci * 32
        cls_idx = u32(dex, o)
        _, no = uleb128(dex, u32(dex, 0x38 + cls_idx * 4))
        end = dex.index(b'\x00', no)
        cls_name = dex[no:end].decode('utf-8', 'replace')
        if cls_name != want_cls:
            continue
        class_data_off = u32(dex, o + 24)
        if class_data_off == 0:
            continue
        cd = class_data_off
        static_fields_size, cd = uleb128(dex, cd)
        instance_fields_size, cd = uleb128(dex, cd)
        direct_methods_size, cd = uleb128(dex, cd)
        virtual_methods_size, cd = uleb128(dex, cd)
        for _ in range(static_fields_size + instance_fields_size):
            _, cd = uleb128(dex, cd)  # field idx diff
            _, cd = uleb128(dex, cd)  # access flags
        for kind, count in (("direct", direct_methods_size), ("virtual", virtual_methods_size)):
            midx = 0
            for _ in range(count):
                diff, cd = uleb128(dex, cd)
                access, cd = uleb128(dex, cd)
                code_off, cd = uleb128(dex, cd)
                midx += diff
                yield cls_name, kind, midx, access, code_off

def disasm_invoke_targets(dex, code_off):
    """Parse a code_item and return (registers_size, insns_size, list of (pc, opcode, idx))."""
    if code_off == 0: return None
    registers = u16(dex, code_off)
    ins = u16(dex, code_off + 2)
    outs = u16(dex, code_off + 4)
    tries = u16(dex, code_off + 6)
    insns_size = u32(dex, code_off + 12)
    insns_off = code_off + 16
    return registers, ins, outs, tries, insns_size, insns_off

def main():
    apk = sys.argv[1]
    cls_want = sys.argv[2] if len(sys.argv) > 2 else "Ldubrowgn/microtimer/MainActivity;"
    meth_want = sys.argv[3] if len(sys.argv) > 3 else None

    z = zipfile.ZipFile(apk)
    dex = None
    for n in z.namelist():
        if n.endswith('.dex') and (n == 'classes.dex' or meth_want):
            dex = z.read(n)
            break
    if dex is None:
        print("NO DEX"); return

    string_ids_off = u32(dex, 0x3c); type_ids_off = u32(dex, 0x44)
    method_ids_size = u32(dex, 0x58); method_ids_off = u32(dex, 0x5c)

    def get_string(idx):
        off = u32(dex, string_ids_off + idx * 4)
        _, o = uleb128(dex, off)
        end = dex.index(b'\x00', o)
        return dex[o:end].decode('utf-8', 'replace')
    def get_type(idx):
        return get_string(u32(dex, type_ids_off + idx * 4))
    methods = []
    for i in range(method_ids_size):
        o = method_ids_off + i * 8
        methods.append((get_type(u16(dex, o)), get_string(u32(dex, o + 4))))

    # also class defs to map method idx -> owning class (first definition wins)
    for cls_name, kind, midx, access, code_off in find_method_code(dex, cls_want, meth_want):
        name = methods[midx][1] if midx < len(methods) else f"?{midx}"
        if meth_want and name != meth_want:
            continue
        if not code_off:
            print(f"{cls_name} {kind} {name} (abstract/native)")
            continue
        registers = u16(dex, code_off)
        ins_size = u32(dex, code_off + 12)
        insns_off = code_off + 16
        print(f"=== {cls_name} {kind} {name} regs={registers} insns={ins_size} ===")
        i = 0
        code = insns_off
        while i < ins_size:
            op = dex[code + i * 2]
            pc = i
            size = 1
            if op == 0x00:  # nop / pseudo
                if code + i*2 + 3 < len(dex) and dex[code + i*2 + 1] == 0x03:  # packed/sparse
                    ident = u16(dex, code + (i+1)*2)
                    size = 4 if ident == 0x0100 else 2
                    if ident == 0x0100:
                        sz = u32(dex, code + (i+2)*2)
                        size = 4 + ((sz * 2) + 1) // 2 + 1 if sz else 4
                    elif ident == 0x0200:
                        size = 2 + u32(dex, code + (i+2)*2)
            elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):  # 35c invokes
                idx = u16(dex, code + (i+1) * 2)
                if idx < len(methods):
                    print(f"  {pc:5d} invoke-{ {0x6e:'virtual',0x6f:'super',0x70:'direct',0x71:'static',0x72:'interface'}[op] } {methods[idx][0]}.{methods[idx][1]}")
                size = 3
            elif op in (0x74, 0x75, 0x76, 0x77, 0x78):  # 3rc
                idx = u16(dex, code + (i+1) * 2)
                if idx < len(methods):
                    print(f"  {pc:5d} invoke-/-range-{ {0x74:'virtual',0x75:'super',0x76:'direct',0x77:'static',0x78:'interface'}[op] } {methods[idx][0]}.{methods[idx][1]}")
                size = 3
            elif op in (0x62, 0x63, 0x69, 0x6a):  # sget/sput families
                idx = u16(dex, code + (i+1) * 2)
                size = 2
            else:
                size = 1
                # standard dalvik sizes would need a table; bounded: treat
                # common 2/3-unit formats via opcode ranges
                if op >= 0x01 and op <= 0x0c: size = 1
                elif op in (0x13,0x16,0x1a,0x1d,0x1e,0x1f,0x22,0x28,0x2b,0x2c) or 0x0d <= op <= 0x12 or 0x23 <= op <= 0x27 or 0x29 <= op <= 0x27: size = 2
                elif op in (0x14,0x17,0x1b,0x1c): size = 3
                elif 0x44 <= op <= 0x51 or 0x52 <= op <= 0x5f or 0x60 <= op <= 0x6d: size = 2
                elif 0x7b <= op <= 0x8f: size = 1
                elif 0x90 <= op <= 0xaf: size = 2
                elif 0xd0 <= op <= 0xd7: size = 2
            i += size
        print()

if __name__ == "__main__":
    main()
