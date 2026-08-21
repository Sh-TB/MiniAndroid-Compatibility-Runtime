#!/usr/bin/env python3
"""EXP-051: Dump bytecode of a specific method from Telegram's DEX files.

Usage: python3 dump_method_bytecode.py "Landroidx/lifecycle/LifecycleRegistry;" "enforceMainThreadIfNeeded"
"""

import os
import sys
import struct
import zipfile

# AOSP standard opcode names (subset).
OPCODE_NAMES = {
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
    0x25: "fill-array-data", 0x26: "throw", 0x27: "goto", 0x28: "goto/16",
    0x29: "goto/32", 0x2a: "packed-switch", 0x2b: "sparse-switch",
    0x2c: "cmpl-float", 0x2d: "cmpg-float", 0x2e: "cmpl-double",
    0x2f: "cmpg-double", 0x30: "cmp-long", 0x31: "if-eq", 0x32: "if-ne",
    0x33: "if-lt", 0x34: "if-ge", 0x35: "if-gt", 0x36: "if-le",
    0x37: "if-eqz", 0x38: "if-nez", 0x39: "if-ltz", 0x3a: "if-gez",
    0x3b: "if-gtz", 0x3c: "if-lez",
    0x44: "aget", 0x45: "aget-wide", 0x46: "aget-object", 0x47: "aget-boolean",
    0x48: "aget-byte", 0x49: "aget-char", 0x4a: "aget-short",
    0x4b: "aput", 0x4c: "aput-wide", 0x4d: "aput-object", 0x4e: "aput-boolean",
    0x4f: "aput-byte", 0x50: "aput-char", 0x51: "aput-short",
    0x52: "iget", 0x53: "iget-wide", 0x54: "iget-object", 0x55: "iget-boolean",
    0x56: "iget-byte", 0x57: "iget-char", 0x58: "iget-short",
    0x59: "iput", 0x5a: "iput-wide", 0x5b: "iput-object", 0x5c: "iput-boolean",
    0x5d: "iput-byte", 0x5e: "iput-char", 0x5f: "iput-short",
    0x60: "sget", 0x61: "sget-wide", 0x62: "sget-object", 0x63: "sget-boolean",
    0x64: "sget-byte", 0x65: "sget-char", 0x66: "sget-short",
    0x67: "sput", 0x68: "sput-wide", 0x69: "sput-object", 0x6a: "sput-boolean",
    0x6b: "sput-byte", 0x6c: "sput-char", 0x6d: "sput-short",
    0x6e: "invoke-virtual", 0x6f: "invoke-super", 0x70: "invoke-direct",
    0x71: "invoke-static", 0x72: "invoke-interface",
    0x74: "invoke-virtual/range", 0x75: "invoke-super/range",
    0x76: "invoke-direct/range", 0x77: "invoke-static/range",
    0x78: "invoke-interface/range",
    0x7b: "neg-un", 0x7c: "neg-int", 0x7d: "not-int",
    0x7e: "neg-long", 0x7f: "not-long", 0x80: "neg-float", 0x81: "neg-double",
    0x82: "int-to-long", 0x83: "int-to-float", 0x84: "int-to-double",
    0x85: "long-to-int", 0x86: "long-to-float", 0x87: "long-to-double",
    0x88: "float-to-int", 0x89: "float-to-long", 0x8a: "float-to-double",
    0x8b: "double-to-int", 0x8c: "double-to-long", 0x8d: "double-to-float",
    0x8e: "int-to-byte", 0x8f: "int-to-char", 0x90: "int-to-short",
    0x91: "add-int", 0x92: "sub-int", 0x93: "mul-int", 0x94: "div-int",
    0x95: "rem-int", 0x96: "and-int", 0x97: "or-int", 0x98: "xor-int",
    0x99: "shl-int", 0x9a: "shr-int", 0x9b: "ushr-int",
    0x9c: "add-int/lit8", 0x9d: "rsub-int/lit8", 0x9e: "mul-int/lit8",
    0x9f: "div-int/lit8", 0xa0: "rem-int/lit8", 0xa1: "and-int/lit8",
    0xa2: "or-int/lit8", 0xa3: "xor-int/lit8", 0xa4: "shl-int/lit8",
    0xa5: "shr-int/lit8", 0xa6: "ushr-int/lit8",
    0xd0: "add-int/lit16", 0xd1: "rsub-int/lit16",
    0xd2: "mul-int/lit16", 0xd3: "div-int/lit16", 0xd4: "rem-int/lit16",
    0xd5: "and-int/lit16", 0xd6: "or-int/lit16", 0xd7: "xor-int/lit16",
    0xe0: "+ipostinc", 0xe1: "+ipreinc", 0xfa: "invoke-polymorphic",
    0xfb: "invoke-polymorphic/range", 0xfc: "invoke-custom",
    0xfd: "invoke-custom/range", 0xfe: "const-method-handle", 0xff: "const-method-type",
}

# Instruction size table (in 16-bit code units). 0 = variable.
# Most opcodes have a fixed size based on format.
INSTRUCTION_SIZE = {}
# 10x: 1 unit
for op in [0x00, 0x0e]: INSTRUCTION_SIZE[op] = 1
# 11x: 1 unit
for op in [0x0d, 0x0f, 0x10, 0x11, 0x1e, 0x1f, 0x22, 0x26, 0x27, 0x28, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c]:
    INSTRUCTION_SIZE[op] = 1
# 12x: 1 unit (move variants)
for op in range(0x01, 0x10): INSTRUCTION_SIZE[op] = 1
# 11n: 1 unit (const/4 = 0x12)
INSTRUCTION_SIZE[0x12] = 1
# 21s: 2 units
for op in [0x13, 0x15, 0x16, 0x17, 0x19, 0x1c, 0x1d]:
    INSTRUCTION_SIZE[op] = 2
# 21h: 2 units
for op in [0x15, 0x19]: INSTRUCTION_SIZE[op] = 2
# 31i: 3 units (const, const/32)
INSTRUCTION_SIZE[0x14] = 3
# 35c: 3 units (invoke-virtual, etc.)
for op in [0x1f, 0x20, 0x22, 0x23, 0x24, 0x6e, 0x6f, 0x70, 0x71, 0x72, 0x25, 0x21]:
    INSTRUCTION_SIZE[op] = 3
# 3rc: 3 units
for op in [0x74, 0x75, 0x76, 0x77, 0x78, 0x26]:  # not 0x26 (throw is 1)
    pass
for op in [0x74, 0x75, 0x76, 0x77, 0x78]:
    INSTRUCTION_SIZE[op] = 3
# 22c: 2 units (instance-of, new-instance, new-array, iget/iput/sget/sput)
for op in [0x1f, 0x20, 0x22, 0x23, 0x21]:
    INSTRUCTION_SIZE[op] = 2
for op in range(0x52, 0x6e):  # iget/iput/sget/sput variants
    INSTRUCTION_SIZE[op] = 2
# 23x: 2 units (array ops, binops)
for op in range(0x44, 0x52): INSTRUCTION_SIZE[op] = 2
for op in range(0x91, 0xa7): INSTRUCTION_SIZE[op] = 2
# 22b: 2 units (binop/lit8)
for op in range(0x9c, 0xa7): INSTRUCTION_SIZE[op] = 2
# 22s: 2 units (binop/lit16)
for op in range(0xd0, 0xd8): INSTRUCTION_SIZE[op] = 2
# 10t: 1 unit (goto)
INSTRUCTION_SIZE[0x27] = 1
# 20t: 2 units (goto/16)
INSTRUCTION_SIZE[0x28] = 2
# 30t: 3 units (goto/32)
INSTRUCTION_SIZE[0x29] = 3
# 31t: 3 units (packed-switch, sparse-switch, fill-array-data)
INSTRUCTION_SIZE[0x2a] = 3
INSTRUCTION_SIZE[0x2b] = 3
INSTRUCTION_SIZE[0x25] = 3
# 21c: 2 units (const-string, const-class, check-cast, new-instance)
INSTRUCTION_SIZE[0x1a] = 2
INSTRUCTION_SIZE[0x1b] = 3  # const-string/jumbo - 31c
INSTRUCTION_SIZE[0x1c] = 2
INSTRUCTION_SIZE[0x1f] = 2  # check-cast
INSTRUCTION_SIZE[0x22] = 2  # new-instance
INSTRUCTION_SIZE[0x23] = 2  # new-array (22c)
# 23x: 2 units (array-length, const ops, binops)
INSTRUCTION_SIZE[0x21] = 2
# 11x: 1 unit (return variants, throw)
INSTRUCTION_SIZE[0x0f] = 1
INSTRUCTION_SIZE[0x10] = 1
INSTRUCTION_SIZE[0x11] = 1
INSTRUCTION_SIZE[0x26] = 1
# 12x: 1 unit
for op in [0x01, 0x02, 0x04, 0x05, 0x07, 0x08, 0x0a, 0x0b, 0x0c, 0x0d]:
    INSTRUCTION_SIZE[op] = 1
# 22x: 2 units (move/from16)
INSTRUCTION_SIZE[0x02] = 2
INSTRUCTION_SIZE[0x05] = 2
INSTRUCTION_SIZE[0x08] = 2
# 32x: 3 units (move/16)
INSTRUCTION_SIZE[0x03] = 3
INSTRUCTION_SIZE[0x06] = 3
INSTRUCTION_SIZE[0x09] = 3
# 31i: 3 units (const, const/high16)
INSTRUCTION_SIZE[0x14] = 3
# 22c: 2 units
for op in range(0x52, 0x6e):
    INSTRUCTION_SIZE[op] = 2
# 35c: 3 units
for op in [0x6e, 0x6f, 0x70, 0x71, 0x72, 0x24, 0x1f, 0x20, 0x21, 0x22, 0x23, 0x25, 0x2a, 0x2b]:
    INSTRUCTION_SIZE[op] = 3
# 3rc: 3 units
for op in [0x74, 0x75, 0x76, 0x77, 0x78]:
    INSTRUCTION_SIZE[op] = 3
# 22b: 2 units
for op in range(0xd0, 0xd8):
    INSTRUCTION_SIZE[op] = 2
# 23x: 2 units (binops)
for op in range(0x91, 0xa7):
    INSTRUCTION_SIZE[op] = 2

def get_size(op, code, pc):
    if op == 0x00:
        # Pseudo goto/Payload header for switch/array-data is NOP + 2 words
        # but in this dump we don't follow jumps.
        return 1
    return INSTRUCTION_SIZE.get(op, 1)

class DexFile:
    def __init__(self, data, name=""):
        self.data = data
        self.name = name
        self._parse_header()
        self._parse_string_ids()
        self._parse_type_ids()
        self._parse_proto_ids()
        self._parse_method_ids()
        self._parse_class_defs()

    def _u32(self, off): return struct.unpack_from("<I", self.data, off)[0]
    def _u16(self, off): return struct.unpack_from("<H", self.data, off)[0]
    def _u8(self, off):  return self.data[off]
    def _read_uleb128(self, off):
        result = 0; shift = 0
        while True:
            b = self.data[off]; off += 1
            result |= (b & 0x7F) << shift
            if b & 0x80 == 0: break
            shift += 7
        return result, off

    def _parse_header(self):
        self.string_ids_size = self._u32(0x38)
        self.string_ids_off  = self._u32(0x3c)
        self.type_ids_size   = self._u32(0x40)
        self.type_ids_off    = self._u32(0x44)
        self.proto_ids_size  = self._u32(0x48)
        self.proto_ids_off   = self._u32(0x4c)
        self.field_ids_size  = self._u32(0x50)
        self.field_ids_off   = self._u32(0x54)
        self.method_ids_size = self._u32(0x58)
        self.method_ids_off  = self._u32(0x5c)
        self.class_defs_size = self._u32(0x60)
        self.class_defs_off  = self._u32(0x64)

    def get_string(self, idx):
        sid_off = self.string_ids_off + idx * 4
        data_off = self._u32(sid_off)
        # First uleb128 = length, then UTF-8 string
        _, end = self._read_uleb128(data_off)
        end = self.data.index(0, end)
        return self.data[end:end].decode("utf-8", errors="replace")

    def _parse_string_ids(self):
        pass  # lazy

    def get_type_descriptor(self, type_idx):
        desc_id_off = self.type_ids_off + type_idx * 4
        desc_str_idx = self._u32(desc_id_off)
        return self.get_string(desc_str_idx)

    def _parse_type_ids(self):
        pass

    def get_method_shorty(self, proto_idx):
        proto_off = self.proto_ids_off + proto_idx * 12
        shorty_idx = self._u32(proto_off)
        return self.get_string(shorty_idx)

    def _parse_proto_ids(self):
        pass

    def get_method_name(self, method_idx):
        m_off = self.method_ids_off + method_idx * 8
        class_idx = self._u16(m_off)
        proto_idx = self._u16(m_off + 2)
        name_idx  = self._u32(m_off + 4)
        return self.get_string(name_idx)

    def get_method_descriptor(self, method_idx):
        m_off = self.method_ids_off + method_idx * 8
        class_idx = self._u16(m_off)
        proto_idx = self._u16(m_off + 2)
        name_idx  = self._u32(m_off + 4)
        return self.get_type_descriptor(class_idx), self.get_string(name_idx)

    def get_method_proto(self, method_idx):
        m_off = self.method_ids_off + method_idx * 8
        proto_idx = self._u16(m_off + 2)
        proto_off = self.proto_ids_off + proto_idx * 12
        shorty_idx = self._u32(proto_off)
        return self.get_string(shorty_idx)

    def _parse_method_ids(self):
        pass

    def _parse_class_defs(self):
        self.classes = []
        for i in range(self.class_defs_size):
            cd_off = self.class_defs_off + i * 32
            class_idx = self._u32(cd_off)
            class_data_off = self._u32(cd_off + 24)
            desc = self.get_type_descriptor(class_idx)
            if class_data_off == 0:
                self.classes.append({"desc": desc, "class_data_off": 0, "methods": []})
                continue
            methods = self._parse_class_data(class_data_off)
            self.classes.append({"desc": desc, "class_data_off": class_data_off, "methods": methods})

    def _parse_class_data(self, off):
        result = {"static_fields": [], "instance_fields": [], "direct_methods": [], "virtual_methods": []}
        static_fields_size, off = self._read_uleb128(off)
        instance_fields_size, off = self._read_uleb128(off)
        direct_methods_size, off = self._read_uleb128(off)
        virtual_methods_size, off = self._read_uleb128(off)
        # Static fields
        prev = 0
        for _ in range(static_fields_size):
            diff, off = self._read_uleb128(off)
            prev += diff
            access, off = self._read_uleb128(off)
            result["static_fields"].append({"field_idx": prev, "access_flags": access})
        prev = 0
        for _ in range(instance_fields_size):
            diff, off = self._read_uleb128(off)
            prev += diff
            access, off = self._read_uleb128(off)
            result["instance_fields"].append({"field_idx": prev, "access_flags": access})
        prev = 0
        for _ in range(direct_methods_size):
            diff, off = self._read_uleb128(off)
            prev += diff
            access, off = self._read_uleb128(off)
            code_off, off = self._read_uleb128(off)
            result["direct_methods"].append({"method_idx": prev, "access_flags": access, "code_off": code_off})
        prev = 0
        for _ in range(virtual_methods_size):
            diff, off = self._read_uleb128(off)
            prev += diff
            access, off = self._read_uleb128(off)
            code_off, off = self._read_uleb128(off)
            result["virtual_methods"].append({"method_idx": prev, "access_flags": access, "code_off": code_off})
        return result

    def find_method(self, class_desc, method_name):
        """Return (dex_index, method_entry, code_off, method_idx) or None."""
        for cls in self.classes:
            if cls["desc"] != class_desc: continue
            for kind in ("direct_methods", "virtual_methods"):
                for m in cls["methods"][kind]:
                    if self.get_method_name(m["method_idx"]) != method_name: continue
                    return m["code_off"], m
        return None, None

    def dump_method(self, class_desc, method_name):
        code_off, m = self.find_method(class_desc, method_name)
        if code_off is None or code_off == 0:
            return f"# {class_desc}.{method_name}: not found or native\n"
        # code_item header: registers_size(u16), ins_size(u16), outs_size(u16),
        # tries_size(u16), debug_info_off(u32), insns_size(u32), insns[insns_size]
        registers_size = self._u16(code_off)
        ins_size = self._u16(code_off + 2)
        outs_size = self._u16(code_off + 4)
        tries_size = self._u16(code_off + 6)
        debug_info_off = self._u32(code_off + 8)
        insns_size = self._u32(code_off + 12)
        insns_off = code_off + 16

        out = []
        out.append(f"# {class_desc}.{method_name}")
        out.append(f"# registers={registers_size} ins={ins_size} outs={outs_size} insns={insns_size}")
        out.append(f"# access_flags=0x{m['access_flags']:x} method_idx={m['method_idx']}")
        out.append("")

        pc = 0
        while pc < insns_size:
            op_off = insns_off + pc * 2
            op = self.data[op_off] | (self.data[op_off + 1] << 8)
            op_low = op & 0xFF
            size = get_size(op_low, self.data, op_off)
            name = OPCODE_NAMES.get(op_low, f"unknown-0x{op_low:02x}")
            line = f"  PC=0x{pc:04x} ({pc:3d})  op=0x{op:04x}  {name}"
            # Decode common args.
            if op_low in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
                if size >= 2:
                    method_idx = self._u16(op_off + 2)
                    cname, mname = self.get_method_descriptor(method_idx)
                    line += f"  → {cname}.{mname}"
            elif op_low in (0x1a, 0x1b):  # const-string
                if size >= 2:
                    str_idx = self._u16(op_off + 2)
                    try:
                        s = self.get_string(str_idx)
                        line += f"  \"{s}\""
                    except Exception:
                        pass
            elif op_low == 0x22:  # new-instance
                if size >= 2:
                    type_idx = self._u16(op_off + 2)
                    line += f"  → {self.get_type_descriptor(type_idx)}"
            elif op_low in (0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
                            0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f,
                            0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,
                            0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d):
                if size >= 2:
                    field_idx = self._u16(op_off + 2)
                    line += f"  field#{field_idx}"
            elif op_low in (0x27, 0x28, 0x29):  # goto
                if op_low == 0x27:
                    offset = (op >> 8) & 0xFF
                    if offset & 0x80: offset -= 256
                    line += f"  +{offset} → PC=0x{pc + offset:04x}"
                elif op_low == 0x28:
                    offset = struct.unpack_from("<h", self.data, op_off + 2)[0]
                    line += f"  +{offset} → PC=0x{pc + offset:04x}"
                else:
                    offset = struct.unpack_from("<i", self.data, op_off + 2)[0]
                    line += f"  +{offset} → PC=0x{pc + offset:04x}"
            elif op_low in (0x31, 0x32, 0x33, 0x34, 0x35, 0x36):
                offset = (op >> 8) & 0xFF
                if offset & 0x80: offset -= 256
                line += f"  v{(op >> 8) >> 4}, v{((op >> 8) & 0xF)} +{offset} → PC=0x{pc + offset:04x}"
            elif op_low in (0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c):
                offset = (op >> 8) & 0xFF
                if offset & 0x80: offset -= 256
                line += f"  v{(op >> 8) & 0xF} +{offset} → PC=0x{pc + offset:04x}"
            out.append(line)
            if size == 0:
                out.append(f"  # unknown size, breaking")
                break
            pc += size
        return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    class_desc = sys.argv[1]
    method_name = sys.argv[2]
    apk_path = sys.argv[3] if len(sys.argv) > 3 else "download/exp038_telegram/Telegram.apk"

    with zipfile.ZipFile(apk_path) as z:
        dex_files = sorted([n for n in z.namelist() if n.endswith(".dex")])
        for dex_name in dex_files:
            data = z.read(dex_name)
            try:
                dex = DexFile(data, dex_name)
            except Exception as e:
                continue
            code_off, m = dex.find_method(class_desc, method_name)
            if code_off is None:
                continue
            print(f"=== Found in {dex_name} ===")
            print(dex.dump_method(class_desc, method_name))
            return
    print(f"# {class_desc}.{method_name}: not found in any DEX")

if __name__ == "__main__":
    main()
