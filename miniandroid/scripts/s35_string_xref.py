#!/usr/bin/env python3
"""S35 R-NEW-334: find which class/method references a target string constant
(ground-truth DEX scan, no androguard).

Usage: s35_string_xref.py <substring> [substring2 ...]
"""
import struct, sys, zipfile

APK = "/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk"


def uleb(d, off):
    r = 0; sh = 0
    while True:
        b = d[off]; off += 1
        r |= (b & 0x7F) << sh; sh += 7
        if not (b & 0x80):
            return r, off


class Dex:
    def __init__(self, d):
        self.d = d
        (self.str_n, self.str_o) = struct.unpack_from("<II", d, 0x38)
        (self.typ_n, self.typ_o) = struct.unpack_from("<II", d, 0x40)
        (self.prt_n, self.prt_o) = struct.unpack_from("<II", d, 0x48)
        (self.fld_n, self.fld_o) = struct.unpack_from("<II", d, 0x50)
        (self.mid_n, self.mid_o) = struct.unpack_from("<II", d, 0x58)
        (self.cls_n, self.cls_o) = struct.unpack_from("<II", d, 0x60)
        self._str_off = [struct.unpack_from("<I", d, self.str_o + i * 4)[0]
                         for i in range(self.str_n)]

    def string(self, i):
        off = self._str_off[i]
        _, p = uleb(self.d, off)
        end = self.d.index(b"\x00", p)
        return self.d[p:end].decode("utf-8", "replace")

    def type(self, i):
        return self.string(struct.unpack_from("<I", self.d, self.typ_o + i * 4)[0])

    def find_string_idx(self, needle):
        return [i for i in range(self.str_n) if needle in self.string(i)]

    def classes(self):
        """yield (class_desc, class_data_off) for classes with data"""
        for i in range(self.cls_n):
            base = self.cls_o + i * 32
            cls_idx = struct.unpack_from("<I", self.d, base)[0]
            data_off = struct.unpack_from("<I", self.d, base + 24)[0]
            yield self.type(cls_idx), data_off

    def class_methods(self, data_off):
        """yield (mid_idx, name, code_off, is_direct)"""
        d = self.d
        p = data_off
        sf, inf, dm_n, vm_n = uleb(d, p)[0], None, None, None
        sf, p = uleb(d, p)
        inf, p = uleb(d, p)
        dm_n, p = uleb(d, p)
        vm_n, p = uleb(d, p)
        fid = 0
        for _ in range(sf):
            fid += uleb(d, p)[0]; p = uleb(d, p)[1]
        for _ in range(inf):
            fid += uleb(d, p)[0]; p = uleb(d, p)[1]
        for kind, n in (("direct", dm_n), ("virtual", vm_n)):
            mid = 0
            for _ in range(n):
                d_ = uleb(d, p); mid += d_[0]; p = d_[1]
                acc = uleb(d, p); p = acc[1]
                co = uleb(d, p); p = co[1]
                yield mid, self.string(struct.unpack_from(
                    "<I", self.d, self.mid_o + mid * 8 + 4)[0]), co[0], kind

    @staticmethod
    def const_strings(code_off, d):
        """return set of string indexes referenced by const-string[/jumbo]"""
        if code_off == 0:
            return set()
        insns_n = struct.unpack_from("<I", d, code_off + 12)[0]
        p = code_off + 16
        end = p + insns_n * 2
        out = set()
        while p + 1 < end:
            op = d[p + 1]
            if op == 0x1A:  # const-string vAA, string@BBBB
                idx = struct.unpack_from("<H", d, p + 2)[0]
                out.add(idx)
                p += 4
            elif op == 0x1B:  # const-string/jumbo
                idx = struct.unpack_from("<I", d, p + 2)[0]
                out.add(idx)
                p += 6
            else:
                # instruction sizes in code units (approx table for common ops)
                sz = INS_SIZE.get(op)
                if sz is None:
                    sz = 1  # unknown: advance 1 (safe-ish scan)
                p += sz * 2
        return out


INS_SIZE = {}
# minimal instruction size table (code units) for scan robustness
for op in range(0x100):
    INS_SIZE[op] = 1
for op in (0x12, 0x13, 0x14, 0x16, 0x54, 0x55, 0x59, 0x5A, 0x5B, 0x5C,
           0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A,
           0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x72,
           0x1A, 0x1D, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26):
    INS_SIZE[op] = 2
for op in (0x15, 0x17, 0x19, 0x52, 0x53, 0x56, 0x57, 0x58, 0x5D, 0x5E,
           0x5F, 0x69, 0x6A):
    INS_SIZE[op] = 2
for op in (0x18,):
    INS_SIZE[op] = 3
for op in (0x00,):
    INS_SIZE[op] = 2  # nop variants can differ; safe
for op in range(0x73, 0x79):
    INS_SIZE[op] = 3
for op in range(0x74, 0x79):
    INS_SIZE[op] = 3
for op in range(0x2B, 0x2D):
    INS_SIZE[op] = 3
for op in (0x28,):
    INS_SIZE[op] = 1
# 35c family (0x60-0x6d covered), 3rc (0x74-0x78 covered)
for op in list(range(0xD0, 0xD3)) + [0xD5, 0xD6, 0xD7, 0xD8, 0xD9,
                                     0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF,
                                     0xE0, 0xE1, 0xE2]:
    INS_SIZE[op] = 2


def main():
    needles = sys.argv[1:]
    z = zipfile.ZipFile(APK)
    dex = Dex(z.read("classes.dex"))
    want = set()
    for n in needles:
        for i in dex.find_string_idx(n):
            want.add(i)
            print(f"# string@{i}: {dex.string(i)[:90]}")
    if not want:
        print("no such strings")
        return
    d = dex.d
    # 1) raw-scan for const-string (1A idx16le) / const-string/jumbo (1B idx32le)
    hits = set()  # file offsets
    for i in want:
        pat16 = bytes([0x1A, i & 0xFF, (i >> 8) & 0xFF])
        p = d.find(pat16)
        while p != -1:
            hits.add(p)
            p = d.find(pat16, p + 1)
        pat32 = bytes([0x1B, i & 0xFF, (i >> 8) & 0xFF, (i >> 16) & 0xFF, (i >> 24) & 0xFF])
        p = d.find(pat32)
        while p != -1:
            hits.add(p)
            p = d.find(pat32, p + 1)
    print(f"# raw const-string sites: {len(hits)}")
    # 2) attribute sites to methods via code-item ranges
    for cls_desc, data_off in dex.classes():
        if data_off == 0:
            continue
        try:
            for mid, name, code_off, kind in dex.class_methods(data_off):
                if code_off == 0:
                    continue
                insns_n = struct.unpack_from("<I", d, code_off + 12)[0]
                lo, hi = code_off + 16, code_off + 16 + insns_n * 2
                if any(lo <= h < hi for h in hits):
                    print(f"HIT {cls_desc} -> {name} ({kind}) code_off={code_off:#x}")
        except Exception:
            continue


if __name__ == "__main__":
    main()
