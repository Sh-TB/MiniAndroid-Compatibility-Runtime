#!/usr/bin/env python3
"""EXP-094: Find and disassemble a method by class+name across all DEX files.
Proper DEX parsing: type_ids → string_ids, method_ids, class_defs → class_data."""
import sys, zipfile, struct

APK = 'download/exp038_telegram/Telegram.apk'

OPN = {
    0x00:"nop",0x01:"move",0x02:"move/from16",0x03:"move/16",0x04:"move-wide",
    0x05:"move-wide/from16",0x06:"move-wide/16",0x07:"move-object",0x08:"move-object/from16",
    0x09:"move-object/16",0x0a:"move-result",0x0b:"move-result-wide",0x0c:"move-result-object",
    0x0d:"move-exception",0x0e:"return-void",0x0f:"return",0x10:"return-wide",
    0x11:"return-object",0x12:"const/4",0x13:"const/16",0x14:"const",0x15:"const/high16",
    0x16:"const-wide/16",0x17:"const-wide/32",0x18:"const-wide",0x19:"const-wide/high16",
    0x1a:"const-string",0x1b:"const-string/jumbo",0x1c:"const-class",0x1d:"monitor-enter",
    0x1e:"monitor-exit",0x1f:"check-cast",0x20:"instance-of",0x21:"array-length",
    0x22:"new-instance",0x23:"new-array",0x24:"filled-new-array",0x25:"filled-new-array/range",
    0x26:"fill-array-data",0x27:"throw",0x28:"goto",0x29:"goto/16",0x2a:"goto/32",
    0x6e:"invoke-virtual",0x6f:"invoke-super",0x70:"invoke-direct",0x71:"invoke-static",
    0x72:"invoke-interface",0x74:"invoke-virtual/range",0x75:"invoke-super/range",
    0x76:"invoke-direct/range",0x77:"invoke-static/range",0x78:"invoke-interface/range",
}
INVOKE = {0x6e,0x6f,0x70,0x71,0x72}
INVOKE_RANGE = {0x74,0x75,0x76,0x77,0x78}

class Dex:
    def __init__(self, data):
        self.d = data
        h = lambda off: struct.unpack_from('<I', data, off)[0]
        # DEX header: 0x38 string_ids_size, 0x3C string_ids_off,
        # 0x40 type_ids_size, 0x44 type_ids_off, 0x48 proto_ids_size, 0x4C proto_ids_off,
        # 0x50 field_ids_size, 0x54 field_ids_off, 0x58 method_ids_size, 0x5C method_ids_off,
        # 0x60 class_defs_size, 0x64 class_defs_off
        self.string_ids_size = h(0x38)
        self.string_ids_off = h(0x3C)
        self.type_ids_size = h(0x40)
        self.type_ids_off = h(0x44)
        self.proto_ids_off = h(0x4C)
        self.field_ids_off = h(0x54)
        self.method_ids_size = h(0x58)
        self.method_ids_off = h(0x5C)
        self.class_defs_size = h(0x60)
        self.class_defs_off = h(0x64)
        # strings cache
        self._str_cache = {}

    def uleb(self, off):
        r=0;s=0
        while True:
            b=self.d[off]; off+=1
            r |= (b&0x7f)<<s
            if not (b&0x80): break
            s+=7
        return r,off

    def get_str(self, idx):
        if idx in self._str_cache: return self._str_cache[idx]
        so = struct.unpack_from('<I', self.d, self.string_ids_off + idx*4)[0]
        ln, p = self.uleb(so)
        end = self.d.index(0, p)
        s = self.d[p:end].decode('utf-8','replace')
        self._str_cache[idx] = s
        return s

    def get_type(self, idx):
        si = struct.unpack_from('<I', self.d, self.type_ids_off + idx*4)[0]
        return self.get_str(si)

    def get_method(self, idx):
        cls_ti, proto_i, name_si = struct.unpack_from('<HHI', self.d, self.method_ids_off + idx*8)
        return self.get_type(cls_ti), self.get_str(name_si), self.proto_str(proto_i)

    def proto_str(self, pi):
        shorty_si, ret_ti, params_off = struct.unpack_from('<III', self.d, self.proto_ids_off + pi*12)
        ret = self.get_type(ret_ti)
        params = []
        if params_off:
            n = struct.unpack_from('<I', self.d, params_off)[0]
            for i in range(n):
                ti = struct.unpack_from('<H', self.d, params_off+4+i*2)[0]
                params.append(self.get_type(ti))
        return "(" + "".join(params) + ")" + ret

    def find_code_off(self, class_desc, method_name):
        """Scan class_defs for the class; scan its methods for name match."""
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i*32
            cls_idx = struct.unpack_from('<I', self.d, off)[0]
            class_data_off = struct.unpack_from('<I', self.d, off+24)[0]
            if self.get_type(cls_idx) != class_desc: continue
            if not class_data_off: continue
            p = class_data_off
            sf,p = self.uleb(p); inf,p = self.uleb(p); dm,p = self.uleb(p); vm,p = self.uleb(p)
            for _ in range(sf):
                _,p = self.uleb(p); _,p = self.uleb(p)
            for _ in range(inf):
                _,p = self.uleb(p); _,p = self.uleb(p)
            for section, count in (('direct',dm),('virtual',vm)):
                prev = 0
                for _ in range(count):
                    diff,p = self.uleb(p); prev += diff
                    _,p = self.uleb(p)
                    code_off,p = self.uleb(p)
                    if code_off:
                        try:
                            c, n, pr = self.get_method(prev)
                            if n == method_name:
                                yield c, n, pr, code_off, section
                        except Exception:
                            pass

    def disasm(self, code_off, max_insn=60):
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', self.d, code_off)
        insns_off = code_off + 16
        out = [f"    regs={regs} ins={ins} outs={outs} insns_size={insns_size}"]
        i = 0
        while i < insns_size and len(out) < max_insn:
            cu = struct.unpack_from('<H', self.d, insns_off + i*2)[0]
            op = cu & 0xFF; hi = (cu>>8)&0xFF
            name = OPN.get(op, f"op_{op:02x}")
            if op in INVOKE:
                A = hi & 0xF; G = hi >> 4
                bidx = struct.unpack_from('<H', self.d, insns_off + (i+1)*2)[0]
                cu3 = struct.unpack_from('<H', self.d, insns_off + (i+2)*2)[0]
                rr = [cu3&0xF,(cu3>>4)&0xF,(cu3>>8)&0xF,(cu3>>12)&0xF][:A]
                if A == 5: rr.append(G)
                try:
                    c,n,pr = self.get_method(bidx)
                    m = f"{c}->{n}{pr}"
                except Exception:
                    m = f"?{bidx}"
                out.append(f"  {i*2:04x}: {name} {{v{', v'.join(map(str,rr))}}}, {m}")
                i += 3; continue
            if op in INVOKE_RANGE:
                A = hi
                bidx = struct.unpack_from('<H', self.d, insns_off + (i+1)*2)[0]
                first = struct.unpack_from('<H', self.d, insns_off + (i+2)*2)[0]
                try:
                    c,n,pr = self.get_method(bidx); m=f"{c}->{n}{pr}"
                except Exception: m=f"?{bidx}"
                out.append(f"  {i*2:04x}: {name} {{v{first}..v{first+A-1}}}, {m}")
                i += 3; continue
            if op == 0x1a:
                bidx = struct.unpack_from('<H', self.d, insns_off + (i+1)*2)[0]
                try: s = self.get_str(bidx)
                except Exception: s = f"?{bidx}"
                out.append(f'  {i*2:04x}: const-string v{hi}, "{s}"')
                i += 2; continue
            if op == 0x12:
                lit4 = (hi>>4)&0xF; lit = lit4-16 if lit4>7 else lit4
                out.append(f"  {i*2:04x}: const/4 v{hi&0xF}, #{lit}")
                i += 1; continue
            if op == 0x13:
                lit = struct.unpack_from('<h', self.d, insns_off + (i+1)*2)[0]
                out.append(f"  {i*2:04x}: const/16 v{hi}, #{lit} (0x{lit&0xFFFF:04x}='{chr(lit) if 32<=lit<127 else '?'}')")
                i += 2; continue
            if op in (0x11,0x0c,0x0a,0x0f):
                out.append(f"  {i*2:04x}: {name} v{hi}")
                i += 1; continue
            if op == 0x0e:
                out.append(f"  {i*2:04x}: return-void"); i += 1; continue
            if op == 0x28:
                out.append(f"  {i*2:04x}: goto +{hi}"); i += 1; continue
            out.append(f"  {i*2:04x}: {name} cu=0x{cu:04x}")
            i += 1; continue
        return "\n".join(out)

def main():
    class_desc = sys.argv[1]
    method_name = sys.argv[2]
    with zipfile.ZipFile(APK) as z:
        for name in sorted(n for n in z.namelist() if n.endswith('.dex')):
            d = z.read(name)
            try: dex = Dex(d)
            except Exception as e: continue
            for c, n, pr, code_off, section in dex.find_code_off(class_desc, method_name):
                print(f"=== {name}: {c}.{n}{pr} [{section}] code_off=0x{code_off:x} ===")
                print(dex.disasm(code_off))

if __name__ == '__main__':
    main()
