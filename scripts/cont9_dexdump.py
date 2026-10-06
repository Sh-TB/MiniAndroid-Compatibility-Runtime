#!/usr/bin/env python3
"""cont9_dexdump.py — fast targeted Dalvik class/method dumper (W5).

Usage:
  cont9_dexdump.py <apk> <Ldesc;>                # list methods
  cont9_dexdump.py <apk> <Ldesc;> <method>       # disassemble method (all overloads)

Scans every classes*.dex, decodes the class_def/method_id/code_item tables
directly. Fast: header-walk only, no full cross-ref.
"""
import sys, zipfile, struct

S = [1]*256
for o in range(0x01,0x0a): S[o]=1
for o in range(0x0a,0x13): S[o]=1
S[0x12]=1; S[0x13]=2; S[0x14]=3; S[0x15]=2
S[0x16]=2; S[0x17]=3; S[0x18]=5; S[0x19]=2
S[0x1a]=2; S[0x1b]=3; S[0x1c]=2; S[0x1d]=1; S[0x1e]=1
S[0x1f]=2; S[0x20]=2; S[0x21]=1; S[0x22]=2; S[0x23]=2
S[0x24]=3; S[0x25]=3; S[0x26]=3; S[0x27]=1
S[0x28]=1; S[0x29]=2; S[0x2a]=3; S[0x2b]=3; S[0x2c]=3
for o in range(0x2d,0x3e): S[o]=2
for o in range(0x3e,0x44): S[o]=1
for o in range(0x44,0x52): S[o]=2
for o in range(0x52,0x5e): S[o]=2
for o in range(0x5e,0x6e): S[o]=2
for o in range(0x6e,0x73): S[o]=3
S[0x73]=1
for o in range(0x74,0x79): S[o]=4
S[0x79]=1; S[0x7a]=1
for o in range(0x7b,0x90): S[o]=1
for o in range(0x90,0xb0): S[o]=2
for o in range(0xb0,0xd0): S[o]=1
for o in range(0xd0,0xd8): S[o]=2
for o in range(0xd8,0xe3): S[o]=2

STR_OPS = {0x1a:1, 0x1b:2}
INVOKE_OPS = {0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
              0x71:'invoke-static',0x72:'invoke-interface',
              0x74:'invoke-virtual/range',0x75:'invoke-super/range',
              0x76:'invoke-direct/range',0x77:'invoke-static/range',
              0x78:'invoke-interface/range'}
IGET_OPS = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
            0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',
            0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',
            0x5d:'iput-byte',0x5e:'iput-short',0x5f:'iget-quickened'}
SFIELD_OPS = {0x60:'sget',0x61:'sget-wide',0x62:'sget-object',0x63:'sget-boolean',
              0x64:'sget-byte',0x65:'sget-char',0x66:'sget-short',
              0x6a:'sput',0x6b:'sput-wide',0x6c:'sput-object',0x6d:'sput-boolean'}


class Dex:
    def __init__(self, b):
        self.b = b
        (self.string_ids_size, self.string_ids_off) = struct.unpack_from('<II', b, 0x38)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', b, 0x40)
        (self.proto_ids_size, self.proto_ids_off) = struct.unpack_from('<II', b, 0x48)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', b, 0x50)
        (self.method_ids_size, self.method_ids_off) = struct.unpack_from('<II', b, 0x58)
        (self.class_defs_size, self.class_defs_off) = struct.unpack_from('<II', b, 0x60)
        self._str_cache = {}

    def u(self, off, n):
        return int.from_bytes(self.b[off:off+n], 'little')

    def uleb(self, off):
        result = 0; shift = 0
        while True:
            byte = self.b[off]; off += 1
            result |= (byte & 0x7f) << shift
            if not (byte & 0x80): break
            shift += 7
        return result, off

    def sleb(self, off):
        result = 0; shift = 0
        while True:
            byte = self.b[off]; off += 1
            result |= (byte & 0x7f) << shift
            shift += 7
            if not (byte & 0x80):
                if byte & 0x40:
                    result -= (1 << shift)
                break
        return result, off

    def string(self, idx):
        if idx in self._str_cache: return self._str_cache[idx]
        if idx >= self.string_ids_size:
            return f"@str{idx}"
        off = self.u(self.string_ids_off + idx*4, 4)
        n, p = self.uleb(off)
        end = self.b.index(b'\x00', p)
        s = self.b[p:end].decode('utf-8', 'replace')
        self._str_cache[idx] = s
        return s

    def type_str(self, idx):
        return self.string(self.u(self.type_ids_off + idx*4, 4))

    def method_ref(self, idx):
        off = self.method_ids_off + idx*8
        cls = self.u(off, 2); proto = self.u(off+2, 2); name = self.u(off+4, 4)
        return self.type_str(cls), self.string(name), self.proto_str(proto)

    def proto_str(self, idx):
        off = self.proto_ids_off + idx*12
        ret = self.u(off+4, 4)  # return_type_idx is u32 at +4? layout: shorty(u32), return(u32), params(u32)
        shorty = self.u(off, 4); return_idx = self.u(off+4, 4); params_off = self.u(off+8, 4)
        params = []
        if params_off:
            n = self.u(params_off, 4)
            for i in range(n):
                params.append(self.type_str(self.u(params_off+4+i*2, 2)))
        return '(' + ','.join(params) + ')' + self.type_str(return_idx)

    def field_ref(self, idx):
        off = self.field_ids_off + idx*8
        cls = self.u(off, 2); ftype = self.u(off+2, 2); name = self.u(off+4, 4)
        return self.type_str(cls), self.string(name), self.type_str(ftype)

    def find_class(self, desc):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i*32
            cls_idx = self.u(off, 4)
            if self.type_str(cls_idx) == desc or self.type_str(cls_idx) == desc+';':
                return off
        return None

    def class_methods(self, class_def_off):
        off = class_def_off
        class_idx = self.u(off, 4)
        access = self.u(off+4, 4)
        super_idx = self.u(off+8, 4)
        src = self.u(off+16, 4)
        ann = self.u(off+20, 4)
        cd_off = self.u(off+24, 4)
        out = {'super': self.type_str(super_idx) if super_idx != 0xffffffff else '?',
               'direct': [], 'virtual': []}
        # interfaces
        iface_off = self.u(off+12, 4)
        ifaces = []
        if iface_off:
            n = self.u(iface_off, 4)
            for i in range(n):
                ifaces.append(self.type_str(self.u(iface_off+4+i*2, 2)))
        out['ifaces'] = ifaces
        if cd_off == 0: return out
        # class_data_item: 4 uleb sizes, then encoded_field arrays, then
        # encoded_method arrays (ALL delta-encoded ulebs).
        p = cd_off
        static_n, p = self.uleb(p)
        inst_n, p = self.uleb(p)
        direct_n, p = self.uleb(p)
        virt_n, p = self.uleb(p)
        # skip static fields
        fidx = 0
        for _ in range(static_n):
            d, p = self.uleb(p); fidx += d
            _, p = self.uleb(p)
        fidx = 0
        for _ in range(inst_n):
            d, p = self.uleb(p); fidx += d
            _, p = self.uleb(p)
        for kind, count in (('direct', direct_n), ('virtual', virt_n)):
            midx = 0
            for _ in range(count):
                dm, p = self.uleb(p); midx += dm
                acc, p = self.uleb(p)
                code, p = self.uleb(p)
                _, mname, mdesc = self.method_ref(midx)
                sz = self.u(code+12, 4) if code else 0
                out[kind].append((mname, mdesc, acc, sz, code))
        return out

    def disasm(self, code_off):
        # code_item layout (Dalvik spec): registers_size u16 @0, ins_size u16
        # @2, outs_size u16 @4, tries_size u16 @6, debug_info_off u32 @8,
        # insns_size u32 @12, insns[] @16.
        regs = self.u(code_off+0, 2)
        ins = self.u(code_off+2, 2)
        outs = self.u(code_off+4, 2)
        tries = self.u(code_off+6, 2)
        dbg = self.u(code_off+8, 4)
        insns_size = self.u(code_off+12, 4)
        insns_off = code_off + 16
        out = [f"    .registers={regs} ins={ins} outs={outs} insns={insns_size}"]
        pc = 0
        while pc < insns_size:
            o = insns_off + pc*2
            word = self.u(o, 2)
            op = word & 0xff
            aa = (word >> 8) & 0xff
            name = f"op{op:#04x}"
            extra = ''
            if op == 0x00:
                if word == 0x0100: name='nop-packed'; sz2=self.u(o+2,2); extra=f" size={sz2}"; S2=0
                elif word == 0x0200: name='nop-sparse'
                else: name='nop'
            elif op == 0x12: name=f"const/4 v{aa&0xf}, {((word>>12)&0xf)}"
            elif op in (0x13,0x16,0x19): name=f"{SFIELD_OPS.get(op,hex(op)) if False else {0x13:'const/16',0x16:'const-wide/16',0x19:'const-wide/high16'}[op]} v{aa}, {self.u(o+2,2)}"
            elif op == 0x14: name=f"const v{aa}, {self.u(o+2,4)}"
            elif op == 0x15: name=f"const/high16 v{aa}, {self.u(o+2,2)}<<16"
            elif op == 0x17: name=f"const-wide/32 v{aa}, {self.u(o+2,4)}"
            elif op == 0x18: name=f"const-wide v{aa}, {self.u(o+2,8)}"
            elif op == 0x1a:
                si = self.u(o+2,2); name=f"const-string v{aa}, \"{self.string(si)[:40]}\""
            elif op == 0x1c: name=f"const-class v{aa}, {self.type_str(self.u(o+2,2))}"
            elif op == 0x1f: name=f"check-cast v{aa}, {self.type_str(self.u(o+2,2))}"
            elif op == 0x20: name=f"instance-of v{aa}, v{(self.u(o+2,2)>>4)&0xf}, {self.type_str(self.u(o+2,2)&0xffff)}" if False else f"instance-of v{aa}"
            elif op == 0x22: name=f"new-instance v{aa}, {self.type_str(self.u(o+2,2))}"
            elif op == 0x23: name=f"new-array v{aa}, v{self.u(o+2,2)&0xff}, {self.type_str((self.u(o+2,2)>>8)&0xffff)}" if False else "new-array"
            elif op == 0x27: name=f"throw v{aa}"
            elif op == 0x28: name=f"goto {aa if aa<0x80 else aa-256:+d}"
            elif op == 0x29:
                d, _ = self.sleb(o+2); name=f"goto/16 {d:+d}"
            elif op == 0x2a:
                d = self.u(o+2,4); name=f"goto/32 {d:+d}"
            elif op in (0x2b,0x2c):
                d = self.u(o+2,4); name=f"{'packed' if op==0x2b else 'sparse'}-switch v{aa}, @{d}"
            elif op in (0x32,0x33,0x34,0x35,0x36,0x37):
                nm = {0x32:'if-eq',0x33:'if-ne',0x34:'if-lt',0x35:'if-ge',0x36:'if-gt',0x37:'if-le'}[op]
                d, _ = self.sleb(o+2)
                name=f"{nm} v{aa}, v{self.u(o+3,1)}, {d:+d}"
            elif op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
                nm = {0x38:'if-eqz',0x39:'if-nez',0x3a:'if-ltz',0x3b:'if-gez',0x3c:'if-gtz',0x3d:'if-lez'}[op]
                d, _ = self.sleb(o+2)
                name=f"{nm} v{aa}, {d:+d}"
            elif op in IGET_OPS:
                fi = self.u(o+2,2)
                try:
                    cls, fn, ft = self.field_ref(fi)
                    name=f"{IGET_OPS[op]} v{aa}, v{(self.u(o+3,1))}, {cls}.{fn}:{ft}"
                except Exception:
                    name=f"{IGET_OPS[op]} v{aa}, v{(self.u(o+3,1))}, @{fi}"
            elif op in SFIELD_OPS:
                fi = self.u(o+2,2)
                try:
                    cls, fn, ft = self.field_ref(fi)
                    name=f"{SFIELD_OPS[op]} v{aa}, {cls}.{fn}:{ft}"
                except Exception:
                    name=f"{SFIELD_OPS[op]} v{aa}, @{fi}"
            elif op in INVOKE_OPS:
                try:
                    mi = self.u(o+2,2)
                    cls, mn, md = self.method_ref(mi)
                    if op < 0x74:
                        name=f"{INVOKE_OPS[op]} {cls}.{mn}{md[:60]}"
                    else:
                        st = self.u(o+4,2); cnt = self.u(o+6,2)
                        name=f"{INVOKE_OPS[op]} {cls}.{mn}{md[:60]} v{st}..v{st+cnt-1}"
                except Exception:
                    name=f"{INVOKE_OPS[op]} @{self.u(o+2,2)}"
            elif op == 0x0e: name="return-void"
            elif op == 0x0f: name=f"return v{aa}"
            elif op == 0x10: name=f"return-wide v{aa}"
            elif op == 0x11: name=f"return-object v{aa}"
            elif op == 0x0a: name=f"move v{aa}, v{self.u(o+3,1)}"
            elif op == 0x0c: name=f"move-object v{aa}, v{self.u(o+3,1)}"
            elif op == 0x0b: name=f"move-result-wide v{aa}"
            elif op == 0x0d: name=f"move-exception v{aa}"
            elif op == 0x0b: name="move-result-wide"
            elif op == 0x0b: pass
            elif op == 0x0c: pass
            else:
                if op in {0x01:1,0x02:1,0x03:1,0x04:1,0x05:1,0x06:1,0x07:1,0x08:1,0x09:1}.keys() and False: pass
            if op == 0x0b: pass
            out.append(f"    {pc*4:#06x}: {name}")
            if op == 0x00 and word == 0x0100:
                sz2 = self.u(o+2,2); pc += 4 + sz2*2; continue
            if op == 0x00 and word == 0x0200:
                sz2 = self.u(o+2,2); pc += 2 + sz2*4; continue
            pc += S[op] if op != 0x00 else 1
        return out


def main():
    apk, desc = sys.argv[1], sys.argv[2]
    meth = sys.argv[3] if len(sys.argv) > 3 else None
    z = zipfile.ZipFile(apk)
    for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        d = Dex(z.read(name))
        off = d.find_class(desc)
        if off is None: continue
        info = d.class_methods(off)
        print(f"== {desc} in {name}")
        print(f"   super={info['super']} ifaces={info['ifaces']}")
        for kind in ('direct','virtual'):
            for mname, mdesc, acc, sz, code in info[kind]:
                flag = 'D' if kind=='direct' else 'V'
                if meth is None:
                    print(f"   [{flag}] {mname}{mdesc}  size={sz}")
                elif mname == meth:
                    print(f"   [{flag}] {mname}{mdesc}  size={sz}")
                    if code:
                        for line in d.disasm(code):
                            print(line)
        return
    print(f"class {desc} NOT FOUND")

if __name__ == '__main__':
    main()
