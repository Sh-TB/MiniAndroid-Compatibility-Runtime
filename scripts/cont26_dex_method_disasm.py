#!/usr/bin/env python3
"""CONT-26: minimal DEX method disassembler (bounded, name-targeted).

Usage: cont26_dex_method_disasm.py <apk> <class-desc-with-slashes> [method-name]
"""
import struct, sys, zipfile

def uleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if (b & 0x80) == 0: break
        shift += 7
    return result, off

def load_dexes(path):
    if path.endswith(".apk"):
        z = zipfile.ZipFile(path)
        return [(n, z.read(n)) for n in z.namelist() if n.endswith(".dex")]
    return [(path.split("/")[-1], open(path, "rb").read())]

class Dex:
    def __init__(self, name, d):
        self.name = name; self.d = d
        (self.string_ids_size, self.string_ids_off,
         self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off,
         self.field_ids_size, self.field_ids_off,
         self.method_ids_size, self.method_ids_off,
         self.class_defs_size, self.class_defs_off) = struct.unpack_from("<12I", d, 56)
    def s(self, idx):
        off = struct.unpack_from("<I", self.d, self.string_ids_off + 4*idx)[0]
        _, o = uleb128(self.d, off)
        end = self.d.index(b"\x00", o)
        return self.d[o:end].decode("utf-8", "replace")
    def t(self, idx):
        si = struct.unpack_from("<I", self.d, self.type_ids_off + 4*idx)[0]
        return self.s(si)
    def methods(self, cls):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32*i
            class_idx, access, sup, ifaces, src, ann, cdata, svals = struct.unpack_from("<8I", self.d, off)
            if self.t(class_idx) != cls: continue
            if not cdata: return
            o = cdata
            sf, o = uleb128(self.d, o)
            inf, o = uleb128(self.d, o)
            dm, o = uleb128(self.d, o)
            vm, o = uleb128(self.d, o)
            n_sf, n_inf, n_dm, n_vm = sf, inf, dm, vm
            last = 0
            for _ in range(n_sf):
                _, o = uleb128(self.d, o)   # field_idx_diff
                _, o = uleb128(self.d, o)   # access_flags
            for _ in range(n_inf):
                _, o = uleb128(self.d, o)   # field_idx_diff
                _, o = uleb128(self.d, o)   # access_flags
            for _ in range(n_dm):
                idx, o = uleb128(self.d, o); idx += last; last = idx
                acc, o = uleb128(self.d, o)
                co, o = uleb128(self.d, o)
                yield self._method(idx, co)
            last = 0
            for _ in range(n_vm):
                idx, o = uleb128(self.d, o); idx += last; last = idx
                acc, o = uleb128(self.d, o)
                co, o = uleb128(self.d, o)
                yield self._method(idx, co)
            return
    def _method(self, midx, code_off):
        if not code_off: return (self._mid(midx), None)
        registers, ins, outs, tries, dbg, insns = struct.unpack_from("<6H", self.d, code_off)
        (insns_size,) = struct.unpack_from("<I", self.d, code_off + 12)
        units = struct.unpack_from(f"<{insns_size}H", self.d, code_off + 16)
        return (self._mid(midx), {"registers": registers, "insns": units, "size": insns_size})
    def _mid(self, idx):
        # method_id_item { u2 class_idx; u2 proto_idx; u4 name_idx; }
        ci, proto = struct.unpack_from("<HH", self.d, self.method_ids_off + 8*idx)
        nm, = struct.unpack_from("<I", self.d, self.method_ids_off + 8*idx + 4)
        return f"{self.t(ci)}.{self.s(nm)} {self.proto(proto)}"
    def proto(self, idx):
        p = self.proto_ids_off + 12*idx
        si, = struct.unpack_from("<I", self.d, p)
        return self.s(si)

OPCODES = {0x00:"nop",0x01:"move",0x12:"const/4",0x13:"const/16",0x14:"const",0x15:"const/high16",
0x16:"const-wide/16",0x1a:"const-string",0x1c:"const-class",0x1d:"monitor-enter",0x1e:"monitor-exit",
0x1f:"check-cast",0x20:"instance-of",0x21:"array-length",0x22:"new-instance",0x23:"new-array",
0x25:"filled-new-array/range",0x26:"fill-array-data",0x27:"throw",0x28:"goto",0x29:"goto/16",
0x2b:"packed-switch",0x2c:"sparse-switch",0x2e:"cmpl-float",0x31:"cmp-long",0x32:"if-eq",0x33:"if-ne",
0x34:"if-lt",0x35:"if-ge",0x36:"if-gt",0x37:"if-le",0x38:"if-eqz",0x39:"if-nez",0x3a:"if-ltz",
0x3b:"if-gez",0x3c:"if-gtz",0x3d:"if-lez",0x44:"aget",0x45:"aget-wide",0x46:"aget-object",0x47:"aget-boolean",
0x4b:"aput",0x4d:"aput-object",0x52:"iget",0x54:"iget-object",0x55:"iget-boolean",0x59:"iput",0x5b:"iput-wide",0x5c:"iput-object",
0x5e:"sget-wide",0x5f:"sget-object",0x60:"sget",0x61:"sget-boolean",0x62:"sget-byte",0x63:"sget-char",0x64:"sget-short",
0x65:"sput",0x66:"sput-wide",0x67:"sput-object",0x68:"sput-boolean",0x69:"sput-byte",
0x6e:"invoke-virtual",0x6f:"invoke-super",0x70:"invoke-direct",0x71:"invoke-static",0x72:"invoke-interface",
0x74:"invoke-virtual/range",0x76:"invoke-direct/range",0x77:"invoke-static/range",0x78:"invoke-interface/range",
0x7b:"int-to-long",0x81:"long-to-int",0x82:"int-to-float",0x85:"int-to-long",0x8f:"int-to-byte",0x90:"int-to-char",0x91:"int-to-short",
0xa0:"add-int",0xb0:"add-int/2addr",0xbb:"sub-long/2addr",0xc8:"sub-float",0xd0:"int-to-long/2addr",
0xda:"mul-int/2addr",0xdb:"mul-long/2addr",0xdf:"div-long/2addr",0xe0:"rem-long/2addr",
0x0a:"move-result",0x0b:"move-result-wide",0x0c:"move-result-object",0x0e:"return-void",0x0f:"return",0x10:"return-wide",0x11:"return-object",
0x04:"move/16",0x07:"move-object",0x08:"move-object/16",0x09:"move-object/16",0x0d:"move-exception",
0x19:"const-wide",0x1b:"const-string/jumbo",}

def disasm(dex, code):
    out = []
    ins = code["insns"]
    i = 0
    def s8(v): return v-256 if v > 0x7f else v
    def s16(v): return v-0x10000 if v > 0x7fff else v
    while i < len(ins):
        unit = ins[i]
        op = unit & 0xff
        name = OPCODES.get(op, f"op-{op:#04x}")
        A = (unit >> 8) & 0xf
        AA = (unit >> 8) & 0xff
        B = (unit >> 12) & 0xf
        if op == 0x00:
            out.append(f"  @{i:#06x} nop"); i += 1; continue
        if op == 0x1a or op == 0x1b:  # const-string[/jumbo] 21c/31c
            if op == 0x1a:
                out.append(f"  @{i:#06x} const-string v{AA}, \"{dex.s(ins[i+1])[:48]}\""); i += 2
            else:
                idx = ins[i+1] | ins[i+2] << 16
                out.append(f"  @{i:#06x} const-string/jumbo v{AA}, \"{dex.s(idx)[:48]}\""); i += 3
            continue
        if op in (0x6e,0x6f,0x70,0x71,0x72):  # 35c
            midx = ins[i+1]
            cnt = (unit >> 12) & 0xf
            g = (unit >> 8) & 0xf
            w = ins[i+2]
            regs = [ (w >> (4*k)) & 0xf for k in range(4) ] + ([g] if cnt == 5 else [])
            regs = regs[:cnt]
            out.append(f"  @{i:#06x} {name} {{{','.join('v'+str(r) for r in regs)}}}, {dex._mid(midx)}"); i += 3; continue
        if op in (0x74,0x76,0x77,0x78):  # 3rc
            midx = ins[i+1]
            cnt = (unit >> 8) & 0xff
            start = ins[i+2]
            out.append(f"  @{i:#06x} {name} {{v{start}..v{start+cnt-1}}}, {dex._mid(midx)}"); i += 3; continue
        if op in (0x52,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,
                  0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):  # 22c field
            fidx = ins[i+1]
            out.append(f"  @{i:#06x} {name} v{A}, v{B}, f@{fidx} ({dex.s(field_name_idx(dex, fidx))})"); i += 2; continue
        if op in (0x1c,0x1f,0x20,0x22,0x23,0x24,0x25,0x27):  # 21c/2x type ops
            tidx = ins[i+1]
            if op == 0x20:  # instance-of: 22c two regs + type
                out.append(f"  @{i:#06x} instance-of v{A}, v{B}, {dex.t(tidx)}")
            elif op == 0x27:
                out.append(f"  @{i:#06x} throw v{AA}")
            else:
                out.append(f"  @{i:#06x} {name} v{AA}, {dex.t(tidx)}")
            i += 2; continue
        if op in (0x32,0x33,0x34,0x35,0x36,0x37):  # 22t branch
            off = s16(ins[i+1])
            out.append(f"  @{i:#06x} {name} v{A}, v{B}, -> @{i+off:#06x}"); i += 2; continue
        if op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):  # 21t branch
            off = s16(ins[i+1])
            out.append(f"  @{i:#06x} {name} v{AA}, -> @{i+off:#06x}"); i += 2; continue
        if op == 0x28:  # 10t
            out.append(f"  @{i:#06x} goto -> @{i+s8(AA):#06x}"); i += 1; continue
        if op == 0x29:  # 20t
            out.append(f"  @{i:#06x} goto/16 -> @{i+s16(ins[i+1]):#06x}"); i += 2; continue
        if op == 0x12:  # 11n const/4
            lit = B;  lit = lit-16 if lit > 7 else lit
            out.append(f"  @{i:#06x} const/4 v{A}, {lit}"); i += 1; continue
        if op in (0x13,0x15,0x16):  # 21s
            out.append(f"  @{i:#06x} {name} v{AA}, {s16(ins[i+1])}"); i += 2; continue
        if op in (0x14,0x17,0x19):  # 31i
            val = ins[i+1] | ins[i+2]<<16 | ins[i+3]<<32
            out.append(f"  @{i:#06x} {name} v{AA}, {val:#x}"); i += 3; continue
        if op == 0x0e: out.append(f"  @{i:#06x} return-void"); i += 1; continue
        if op in (0x0a,0x0b,0x0c,0x0d,0x0f,0x10,0x11):
            out.append(f"  @{i:#06x} {name} v{AA}"); i += 1; continue
        if op in (0x01,0x04,0x07,0x08,0x09):  # 12x move family
            out.append(f"  @{i:#06x} {name} v{A}, v{B}"); i += 1; continue
        if op in (0x0e,): i += 1; continue
        if op == 0x26:  # fill-array-data payload: 31c
            out.append(f"  @{i:#06x} fill-array-data v{AA}, -> @{i + (ins[i+1]|ins[i+2]<<16)*2:#06x} (units)"); i += 3; continue
        if op in (0x2b,0x2c):  # 31t
            out.append(f"  @{i:#06x} {name} v{AA}, -> payload"); i += 3; continue
        if op in (0x7b,0x81,0x82,0x85,0x8f,0x90,0x91):
            out.append(f"  @{i:#06x} {name} v{B}, v{A}"); i += 1; continue
        if op in (0xb0,0xbb,0xda,0xdb,0xdf,0xe0):
            out.append(f"  @{i:#06x} {name} v{A}, v{B}"); i += 1; continue
        out.append(f"  @{i:#06x} {name} unit={unit:#06x} next={ins[i+1] if i+1 < len(ins) else 0:#x}")
        i += 1
    return out

def method_name_idx(dex, midx):
    mi, = struct.unpack_from("<H", dex.d, dex.method_ids_off + 8*midx + 2)
    return mi
def method_cls_idx(dex, midx):
    ci, = struct.unpack_from("<H", dex.d, dex.method_ids_off + 8*midx)
    return ci
def field_name_idx(dex, fidx):
    fi, = struct.unpack_from("<H", dex.d, dex.field_ids_off + 8*fidx + 2)
    return fi

def main():
    path, cls = sys.argv[1], sys.argv[2]
    want = sys.argv[3] if len(sys.argv) > 3 else None
    for name, data in load_dexes(path):
        dx = Dex(name, data)
        for (msig, code) in dx.methods(cls):
            if code is None: continue
            mname = msig.split('.')[1].split(' ')[0]
            if want and want not in mname: continue
            print(f"[{name}] {msig} regs={code['registers']} size={code['size']}")
            for line in disasm(dx, code): print(line)
            print()

if __name__ == "__main__":
    main()
