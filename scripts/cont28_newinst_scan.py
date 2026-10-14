#!/usr/bin/env python3
"""cont28_newinst_scan.py — find every new-instance + invoke-direct site for a
given class descriptor across all DEX files of an APK. AUTHORITY: the APK's own
DEX bytecode (SOURCE-FIRST ground truth when upstream sources are unavailable).

usage: cont28_newinst_scan.py <apk> <class-descriptor>
example: cont28_newinst_scan.py run/w8/oracle12.apk Landroidx/compose/ui/graphics/layer/GraphicsLayer;
"""
import struct, sys, zipfile, re

def uleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def sleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80):
            if b & 0x40: result -= (1 << shift)
            break
    return result, off

class Dex:
    def __init__(self, name, d):
        self.name = name; self.d = d
        self.string_ids_size = struct.unpack_from("<I", d, 0x38)[0]
        self.string_ids_off = struct.unpack_from("<I", d, 0x3c)[0]
        self.type_ids_size = struct.unpack_from("<I", d, 0x40)[0]
        self.type_ids_off = struct.unpack_from("<I", d, 0x44)[0]
        self.proto_ids_off = struct.unpack_from("<I", d, 0x4c)[0]
        self.field_ids_off = struct.unpack_from("<I", d, 0x54)[0]
        self.method_ids_off = struct.unpack_from("<I", d, 0x5c)[0]
        self.class_defs_off = struct.unpack_from("<I", d, 0x64)[0]
        self.class_defs_size = struct.unpack_from("<I", d, 0x60)[0]

    def s(self, idx):
        off = struct.unpack_from("<I", self.d, self.string_ids_off + 4*idx)[0]
        n, o = uleb128(self.d, off)
        end = self.d.index(b"\x00", o)
        return self.d[o:end].decode("utf-8", "replace")

    def t(self, idx):
        return self.s(struct.unpack_from("<I", self.d, self.type_ids_off + 4*idx)[0])

    def f(self, idx):
        ci, si = struct.unpack_from("<HH", self.d, self.field_ids_off + 8*idx)
        return f"{self.t(ci)}.{self.s(si)}"

    def m(self, idx):
        base = self.method_ids_off + 8*idx
        ci = struct.unpack_from("<H", self.d, base)[0]
        pi = struct.unpack_from("<H", self.d, base+2)[0]
        si = struct.unpack_from("<I", self.d, base+4)[0]
        # proto: shorty_idx, return_type_idx, parameters_off
        params_off = struct.unpack_from("<I", self.d, self.proto_ids_off + 12*pi + 8)[0]
        ret = self.t(struct.unpack_from("<H", self.d, self.proto_ids_off + 12*pi + 4)[0])
        params = ""
        if params_off:
            n, o = uleb128(self.d, params_off)
            ps = [self.t(struct.unpack_from("<H", self.d, params_off + 4 + 2*i)[0]) for i in range(n)]
            params = "".join(ps)
        return f"{self.t(ci)}.{self.s(si)}({params}){ret}"

    def classes(self):
        for i in range(self.class_defs_size):
            ci = struct.unpack_from("<I", self.d, self.class_defs_off + 32*i)[0]
            yield self.t(ci), self.class_defs_off + 32*i

    def method_code(self, cd_off):
        """Yield (msig, codeitem_dict) for direct+virtual methods of class at cd_off."""
        d = self.d
        acc = struct.unpack_from("<I", d, cd_off + 4)[0]  # access_flags (unused here)
        # class_data_off
        class_data_off = struct.unpack_from("<I", d, cd_off + 24)[0]
        if not class_data_off: return
        off = class_data_off
        sf, inf, dm, vm, _ = None, None, None, None, None
        sf, off = uleb128(d, off); inf, off = uleb128(d, off)
        dm, off = uleb128(d, off); vm, off = uleb128(d, off)
        # static fields
        fidx = 0
        for _ in range(sf):
            di, off = uleb128(d, off); fidx += di
            _, off = uleb128(d, off)
        # instance fields
        for _ in range(inf):
            di, off = uleb128(d, off); fidx += di
            _, off = uleb128(d, off)
        # direct methods
        midx = 0
        for _ in range(dm):
            di, off = uleb128(d, off); midx += di
            acc2, off = uleb128(d, off)
            co, off = uleb128(d, off)
            yield self.m(midx), co, acc2
        midx = 0
        for _ in range(vm):
            di, off = uleb128(d, off); midx += di
            acc2, off = uleb128(d, off)
            co, off = uleb128(d, off)
            yield self.m(midx), co, acc2

def parse_code_item(d, co):
    """Parse a code_item; returns dict or None for abstract/native."""
    if co == 0: return None
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from("<HHHHII", d, co)
    insns_off = co + 16
    if insns_size == 0: return None
    return dict(regs=regs, ins=ins, outs=outs, tries=tries,
                insns=insns_off, size=insns_size)

def disasm_scan(dx, code, want_cls):
    """Walk instruction stream with CORRECT widths; return new-instance rows
    of want_cls."""
    d = dx.d; out = []
    from cont28_disasm import W
    off = code["insns"]; end = off + code["size"]*2
    while off < end:
        op = d[off]
        w = W[op]
        try:
            if op == 0x22:  # new-instance
                ti = struct.unpack_from("<H", d, off+2)[0]
                cls = dx.t(ti)
                if cls == want_cls:
                    out.append((off - code["insns"], "new-instance", cls))
        except Exception:
            pass
        off += w*2
    return out

def main():
    apk, want = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(apk)
    for n in z.namelist():
        if not n.endswith(".dex"): continue
        dx = Dex(n, z.read(n))
        for cls, cd_off in dx.classes():
            for msig, co, acc in dx.method_code(cd_off):
                code = parse_code_item(dx.d, co)
                if not code: continue
                hits = disasm_scan(dx, code, want)
                if hits:
                    print(f"[{dx.name}] {msig}")
                    for h in hits: print(f"   @{h[0]:#06x} {h[1]} {h[2]}")

if __name__ == "__main__":
    main()
