#!/usr/bin/env python3
"""s122_dexdump.py — minimal correct DEX method bytecode dumper.
Usage: s122_dexdump.py <apk> <class-desc> <method-name>
Decodes invoke-* (class.name), iget/iput/sget/sput (field), const-string,
new-instance, instance-of; prints raw cu words otherwise."""
import struct
import sys
import zipfile


def uleb128(buf, off):
    result = 0
    shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, off


class Dex:
    def __init__(self, data, name):
        self.data = data
        self.name = name
        (self.magic, self.checksum, sig, fsize, hed_off, endian,
         link_size, link_off, map_off, str_ids, str_ids_off,
         type_ids, type_ids_off, proto_ids, proto_ids_off,
         field_ids, field_ids_off, method_ids, method_ids_off,
         class_defs, class_defs_off, data_size, data_off) = struct.unpack_from(
            "<8sI20sIIIIIIIIIIIIIIIIIIII", data, 0)
        self.method_ids = method_ids
        self.class_defs_size = class_defs
        self.class_defs_off = class_defs_off
        self.method_ids_off = method_ids_off
        self.field_ids = field_ids
        self.field_ids_off = field_ids_off
        self.str_ids = str_ids
        self.str_ids_off = str_ids_off
        self.type_ids = type_ids
        self.type_ids_off = type_ids_off

    def _u32(self, off):
        try:
            return struct.unpack_from("<I", self.data, off)[0]
        except struct.error:
            return 0

    def _u16(self, off):
        try:
            return struct.unpack_from("<H", self.data, off)[0]
        except struct.error:
            return 0

    def string(self, idx):
        off = self._u32(self.str_ids_off + 4 * idx)
        if off >= len(self.data):
            return f"<str#{idx}>"
        _n, p = uleb128(self.data, off)
        end = self.data.index(b"\x00", p)
        return self.data[p:end].decode("utf-8", "replace")

    def type_desc(self, idx):
        return self.string(self._u32(self.type_ids_off + 4 * idx))

    def method(self, idx):
        off = self.method_ids_off + 8 * idx
        cls_t = self._u16(off)
        name_s = self._u32(off + 4)
        return f"{self.type_desc(cls_t)}.{self.string(name_s)}"

    def field(self, idx):
        off = self.field_ids_off + 8 * idx
        cls_t = self._u16(off)
        name_s = self._u16(off + 4)
        return f"{self.type_desc(cls_t)}.{self.string(name_s)}"

    INVOKE_OPS = {0x6E: "invoke-virtual", 0x6F: "invoke-super",
                  0x70: "invoke-direct", 0x71: "invoke-static",
                  0x72: "invoke-interface", 0x74: "invoke-virtual/range",
                  0x75: "invoke-super/range", 0x76: "invoke-direct/range",
                  0x77: "invoke-static/range", 0x78: "invoke-interface/range"}
    FIELD_OPS = {0x52: "iget", 0x53: "iget-wide", 0x54: "iget-object",
                 0x55: "iget-boolean", 0x56: "iget-byte", 0x57: "iget-char",
                 0x58: "iget-short", 0x59: "iput", 0x5A: "iput-wide",
                 0x5B: "iput-object", 0x5C: "iput-boolean", 0x5D: "iput-byte",
                 0x5E: "iput-char", 0x5F: "iput-short", 0x60: "sget",
                 0x61: "sget-wide", 0x62: "sget-object", 0x63: "sget-boolean",
                 0x64: "sget-byte", 0x65: "sget-char", 0x66: "sget-short",
                 0x67: "sput", 0x68: "sput-wide", 0x69: "sput-object",
                 0x6A: "sput-boolean", 0x6B: "sput-byte", 0x6C: "sput-char",
                 0x6D: "sput-short"}
    SZ2_35C = {0x20: 2, 0x21: 2, 0x22: 2, 0x23: 3, 0x24: 3, 0x25: 3,
               0x26: 3, 0x1F: 2, 0x1C: 2, 0x1A: 2, 0x1B: 3, 0x13: 2,
               0x14: 2, 0x15: 2, 0x16: 2, 0x17: 2, 0x18: 3, 0x19: 2}
    # instruction sizes in 16-bit code units by low opcode (spec tables)
    SIZES = {}
    for _o in range(0x00, 0x12):
        SIZES[_o] = 1
    for _o in (0x12, 0x13, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23):
        SIZES[_o] = 1 if _o == 0x12 else 2
    for _o in range(0x27, 0x2D):
        SIZES[_o] = 1
    SIZES[0x28] = 1
    SIZES[0x14] = 3  # const vAA, #+BBBBBBBB
    SIZES[0x29] = 2
    SIZES[0x2A] = 3
    SIZES[0x2B] = 3
    SIZES[0x2C] = 3
    for _o in range(0x2D, 0x45):
        SIZES[_o] = 2
    for _o in range(0x44, 0x6E):
        SIZES[_o] = 2
    for _o in range(0x6E, 0x79):
        SIZES[_o] = 3
    for _o in range(0x7B, 0x90):
        SIZES[_o] = 1
    for _o in range(0x90, 0xB1):
        SIZES[_o] = 2
    for _o in range(0xB0, 0xD0):
        SIZES[_o] = 1
    for _o in range(0xD0, 0xE3):
        SIZES[_o] = 2

    def dump_method(self, cls, meth, ctx=12):
        for cd in range(self.class_defs):
            cd_off = self._u32(self.__dict__.get("_cdo", 0) or 0)  # placeholder
        # class defs parsed on demand
        n = self._u32(0x60) if False else None
        return None

    def iter_classes(self, class_defs_size, class_defs_off):
        for i in range(class_defs_size):
            off = class_defs_off + 32 * i
            cls_idx = self._u16(off)
            class_data_off = self._u32(off + 24)
            yield self.type_desc(cls_idx), class_data_off

    def find_code(self, cls, meth, class_defs_size, class_defs_off):
        for desc, cdo in self.iter_classes(class_defs_size, class_defs_off):
            if desc != cls or cdo == 0:
                continue
            off = cdo
            sfc, off = uleb128(self.data, off)
            ifc, off = uleb128(self.data, off)
            dmc, off = uleb128(self.data, off)
            vmc, off = uleb128(self.data, off)
            fidx = 0
            for _ in range(sfc + ifc):  # walk past encoded_fields
                d, off = uleb128(self.data, off)
                _acc, off = uleb128(self.data, off)
                fidx += d
            for kind, cnt in (("direct", dmc), ("virtual", vmc)):
                midx = 0  # per DEX spec the diff resets at each list start
                for _ in range(cnt):
                    d, off = uleb128(self.data, off)
                    acc, off = uleb128(self.data, off)
                    code_off, off = uleb128(self.data, off)
                    midx += d
                    if self._method_name(midx) == meth and code_off:
                        return code_off
        return None

    def _method_name(self, midx):
        return self.string(self._u32(self.method_ids_off + 8 * midx + 4))


def main():
    apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    with zipfile.ZipFile(apk) as z:
        for dn in sorted(n for n in z.namelist() if n.endswith(".dex")):
            dx = Dex(z.read(dn), dn)
            dx.class_defs_size = dx._u32(0x60)  # class_defs_size is at 0x60
            dx.class_defs_off = dx._u32(0x64)
            code_off = dx.find_code(cls, meth, dx.class_defs_size if hasattr(dx,'class_defs_size') else None,
                                    dx.class_defs_off)
            if not code_off:
                continue
            regs = dx._u16(code_off)
            ins_sz = dx._u16(code_off + 2)
            outs = dx._u16(code_off + 4)
            insns = dx._u32(code_off + 12)
            insns_off = code_off + 16
            print(f"=== {cls}.{meth} in {dn} regs={regs} ins={ins_sz} "
                  f"outs={outs} insns={insns} ===")
            pc = 0
            while pc < insns:
                cu = dx._u16(insns_off + pc * 2)
                op = cu & 0xFF
                size = Dex.SIZES.get(op, 0)
                txt = ""
                if op in Dex.INVOKE_OPS:
                    midx = dx._u16(insns_off + pc * 2 + 2)
                    txt = f"→ {dx.method(midx)}"
                elif op in Dex.FIELD_OPS:
                    fidx = dx._u16(insns_off + pc * 2 + 2)
                    txt = f"→ {dx.field(fidx)}"
                elif op in (0x1A, 0x1B):
                    sidx = dx._u16(insns_off + pc * 2 + 2)
                    try:
                        txt = f"\"{dx.string(sidx)}\""
                    except Exception:
                        txt = f"str#{sidx}"
                elif op == 0x22:
                    tidx = dx._u16(insns_off + pc * 2 + 2)
                    txt = f"new {dx.type_desc(tidx)}"
                elif op == 0x20:
                    tidx = dx._u16(insns_off + pc * 2 + 2)
                    txt = f"instance-of {dx.type_desc(tidx)}"
                print(f"PC={pc:4d}  op=0x{op:02x}  "
                      f"{Dex.INVOKE_OPS.get(op, Dex.FIELD_OPS.get(op, ''))}"
                      f"  {txt}")
                if size == 0:
                    print(f"  # unknown op 0x{op:02x}, stop")
                    break
                pc += size
            return
    print(f"{cls}.{meth}: not found")


if __name__ == "__main__":
    main()
