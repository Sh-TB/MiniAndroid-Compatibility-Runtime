#!/usr/bin/env python3
"""CONT-124 decode tool: dump class defs (super + interfaces) and methods of
R8-renamed classes from an APK's DEX. Ground truth for hierarchy-law fixes.

Usage:
  python3 scripts/c124_dex_classdef.py <apk> <Ldesc;> [Ldesc2; ...]
  python3 scripts/c124_dex_classdef.py <apk> --subclassof <Ldesc;>   # find classes whose super==desc
  python3 scripts/c124_dex_classdef.py <apk> --method <Lcls;> <name> # dump method code size
"""
import struct, sys, zipfile


class Dex:
    def __init__(self, data):
        self.d = data
        self.ssz, self.soff = struct.unpack_from('<II', data, 0x38)
        self.tsz, self.toff = struct.unpack_from('<II', data, 0x40)
        psz, self.poff = struct.unpack_from('<II', data, 0x48)
        self.msz, self.moff = struct.unpack_from('<II', data, 0x58)
        self.fsz, self.foff = struct.unpack_from('<II', data, 0x50)
        self.csz, self.coff = struct.unpack_from('<II', data, 0x60)
        self._str = {}
        self._types = {}

    def s(self, idx):
        if idx in self._str:
            return self._str[idx]
        off = struct.unpack_from('<I', self.d, self.soff + 4 * idx)[0]
        p, shift, ln = off, 0, 0
        while True:
            b = self.d[p]; p += 1; ln |= (b & 0x7f) << shift; shift += 7
            if not b & 0x80:
                break
        v = self.d[p:p + ln].decode('utf-8', 'replace')
        self._str[idx] = v
        return v

    def t(self, idx):
        if idx not in self._types:
            self._types[idx] = self.s(struct.unpack_from('<I', self.d, self.toff + 4 * idx)[0])
        return self._types[idx]

    def uleb(self, p):
        shift = v = 0
        while True:
            b = self.d[p]; p += 1; v |= (b & 0x7f) << shift; shift += 7
            if not b & 0x80:
                break
        return v, p

    def classes(self):
        for i in range(self.csz):
            base = self.coff + 32 * i
            cidx = struct.unpack_from('<I', self.d, base)[0]
            aidx = struct.unpack_from('<I', self.d, base + 4)[0]
            sidx = struct.unpack_from('<I', self.d, base + 8)[0]
            ifoff = struct.unpack_from('<I', self.d, base + 12)[0]
            cdoff = struct.unpack_from('<I', self.d, base + 24)[0]
            sup = self.t(sidx) if sidx != 0xFFFFFFFF else '<none>'
            ifaces = []
            if ifoff:
                ifsz = struct.unpack_from('<I', self.d, ifoff)[0]
                ifaces = [self.t(struct.unpack_from('<H', self.d, ifoff + 4 + 2 * k)[0])
                          for k in range(ifsz)]
            yield dict(desc=self.t(cidx), access=aidx, sup=sup, ifaces=ifaces,
                       cdoff=cdoff, base=base)

    def class_methods(self, cdoff):
        """Yield (name, proto, code_off) direct+virtual methods of a class_data blob."""
        d = self.d
        p = cdoff
        sf, p = self.uleb(p)
        inf, p = self.uleb(p)
        dm, p = self.uleb(p)
        vm, p = self.uleb(p)
        for _ in range(sf):
            _, p = self.uleb(p)  # field idx diff
            _, p = self.uleb(p)  # access
        for _ in range(inf):
            _, p = self.uleb(p)  # field idx diff
            _, p = self.uleb(p)  # access
        midx = 0
        for _ in range(dm):
            diff, p = self.uleb(p)
            acc, p = self.uleb(p)
            coff, p = self.uleb(p)
            midx += diff
            if coff:
                m = self.method_info(midx, coff)
                if m:
                    yield m
        midx = 0
        for _ in range(vm):
            diff, p = self.uleb(p)
            acc, p = self.uleb(p)
            coff, p = self.uleb(p)
            midx += diff
            if coff:
                m = self.method_info(midx, coff)
                if m:
                    yield m

    def method_info(self, midx, code_off):
        if midx >= self.msz:
            return None
        mb = self.moff + 8 * midx
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, mb)
        # code_item: registers(2) ins(2) outs(2) tries(2) debug(4) insns(4)...
        regs, ins, outs, tries = struct.unpack_from('<HHHH', self.d, code_off)
        insns_sz = struct.unpack_from('<I', self.d, code_off + 12)[0]
        return dict(cls=self.t(cidx), name=self.s(nidx),
                    proto=self.proto_str(pidx), code=code_off,
                    regs=regs, ins=ins, outs=outs, insns=insns_sz)

    def field_id(self, idx):
        fb = self.foff + 8 * idx
        cidx, tidx, nidx = struct.unpack_from('<HHI', self.d, fb)
        return dict(cls=self.t(cidx), type=self.t(tidx), name=self.s(nidx))

    def method_id(self, idx):
        mb = self.moff + 8 * idx
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, mb)
        return dict(cls=self.t(cidx), name=self.s(nidx))

    def insns(self, code_off, n_words):
        """Yield (pc_word, w0, w1, w2) raw instruction words."""
        base = code_off + 16
        for i in range(n_words):
            w0 = struct.unpack_from('<H', self.d, base + 2 * i)[0]
            w1 = struct.unpack_from('<H', self.d, base + 2 * i + 2)[0] if i + 1 < n_words else 0
            w2 = struct.unpack_from('<H', self.d, base + 2 * i + 4)[0] if i + 2 < n_words else 0
            yield i, w0, w1, w2

    def proto_str(self, pidx):
        pb = self.poff + 12 * pidx
        sidx, ridx = struct.unpack_from('<II', self.d, pb)
        # proto_id: shorty(4) return(4) params(4)
        ret = self.t(struct.unpack_from('<I', self.d, self.poff + 12 * pidx + 4)[0])
        po = struct.unpack_from('<I', self.d, self.poff + 12 * pidx + 8)[0]
        n = struct.unpack_from('<I', self.d, po)[0] if po else 0
        ps = [self.t(struct.unpack_from('<H', self.d, po + 2 + 2 * k)[0]) for k in range(n)] if po else []
        return '(' + ''.join(ps) + ')' + ret


def main():
    apk = sys.argv[1]
    args = sys.argv[2:]
    z = zipfile.ZipFile(apk)
    mode = 'classes'
    targets, subclassof, method_req = [], None, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--subclassof':
            subclassof = args[i + 1]; i += 2
        elif a == '--method':
            method_req = (args[i + 1], args[i + 2]); i += 3
        elif a == '--scan-alloc':
            mode = 'scan'; i += 1
        else:
            targets.append(a); i += 1
    dexes = [n for n in z.namelist() if n.endswith('.dex')]
    dexobjs = [(n, Dex(z.read(n))) for n in dexes]
    if mode == 'scan':
        sys.path.insert(0, '/home/z/my-project/miniandroid/tools')
        import dump_method_bytecode as dmp
        want = set(targets)
        for dn, dx in dexobjs:
            for c in dx.classes():
                if not c['cdoff']:
                    continue
                for m in dx.class_methods(c['cdoff']):
                    if not m['insns'] or m['code'] <= 0:
                        continue
                    base = m['code'] + 16
                    pc = 0
                    while pc < m['insns']:
                        op_off = base + pc * 2
                        if op_off + 4 > len(dx.d):
                            break
                        w0 = dx.d[op_off] | (dx.d[op_off + 1] << 8)
                        opl = w0 & 0xFF
                        sz = dmp.get_size(opl, dx.d, op_off)
                        if sz <= 0 or pc + sz > m['insns']:
                            break
                        if opl == 0x22 and sz >= 2:
                            tidx = struct.unpack_from('<H', dx.d, op_off + 2)[0]
                            if tidx >= dx.tsz:
                                pc += sz; continue
                            desc = dx.t(tidx)
                            if desc in want:
                                print(f"new-instance {desc} at {m['cls']}.{m['name']} {m['proto']} code={m['code']:#x}")
                        elif opl == 0x23 and sz >= 2:
                            tidx = struct.unpack_from('<H', dx.d, op_off + 2)[0]
                            if tidx >= dx.tsz:
                                pc += sz; continue
                            desc = dx.t(tidx)
                            if desc in want or (desc.startswith('[') and desc[1:] in want):
                                print(f"new-array {desc} at {m['cls']}.{m['name']} {m['proto']} code={m['code']:#x}")
                        elif opl == 0x1C and sz >= 2:
                            tidx = struct.unpack_from('<H', dx.d, op_off + 2)[0]
                            if tidx >= dx.tsz:
                                pc += sz; continue
                            desc = dx.t(tidx)
                            if desc in want:
                                print(f"const-class {desc} at {m['cls']}.{m['name']} {m['proto']} code={m['code']:#x}")
                        elif opl in (0x70, 0x71) and sz >= 3:
                            midx2 = struct.unpack_from('<H', dx.d, op_off + 2)[0]
                            if midx2 < dx.msz:
                                mi = dx.method_id(midx2)
                                if mi['cls'] in want:
                                    print(f"invoke {mi['cls']}.{mi['name']} at {m['cls']}.{m['name']} {m['proto']} code={m['code']:#x}")
                        pc += sz
        return
    if method_req:
        cls, name = method_req
        for dn, dx in dexobjs:
            for c in dx.classes():
                if c['desc'] == cls:
                    for m in dx.class_methods(c['cdoff']):
                        if m['name'] == name:
                            print(f"{dn} {cls}.{name}{m['proto']} code_off={m['code']:#x} regs={m['regs']} ins={m['ins']} outs={m['outs']} insns={m['insns']}")
        return
    for dn, dx in dexobjs:
        for c in dx.classes():
            if subclassof and c['sup'] == subclassof:
                print(f"{c['desc']}: super={c['sup']} ifaces={c['ifaces']}")
            elif not subclassof and c['desc'] in targets:
                print(f"{c['desc']}: super={c['sup']} ifaces={c['ifaces']}")


if __name__ == '__main__':
    main()
