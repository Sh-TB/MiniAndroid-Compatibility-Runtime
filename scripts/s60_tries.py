#!/usr/bin/env python3
"""s60_tries.py <apk> <Ldesc;> <method> — print the code_item try/catch blocks."""
import sys, zipfile, struct
sys.path.insert(0, "/home/z/my-project/scripts")

apk, cls, meth = sys.argv[1], sys.argv[2], sys.argv[3]
zf = zipfile.ZipFile(apk)
TYPE_IDS = METH_IDS = None


def uleb(buf, off):
    r = s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if not b & 0x80: return r, off
        s += 7


def find_method(data):
    # header
    string_ids = struct.unpack_from('<I', data, 56)[0]
    type_ids = struct.unpack_from('<I', data, 64)[0]
    proto_ids = struct.unpack_from('<I', data, 72)[0]
    field_ids = struct.unpack_from('<I', data, 80)[0]
    method_ids = struct.unpack_from('<I', data, 88)[0]
    data_off = struct.unpack_from('<I', data, 104)[0]
    # strings
    def get_str(idx):
        so = struct.unpack_from('<I', data, 96 + 4*idx)[0]
        n, o = uleb(data, so)
        raw = data[o:o+ (n*4 if False else n)]  # mutf8 approx
        # decode MUTF-8 crudely
        out = []
        i = 0
        while i < n and i < len(raw):
            b = raw[i]
            if b < 0x80:
                out.append(chr(b)); i += 1
            elif b >> 5 == 0b110:
                out.append(chr(((b & 0x1f) << 6) | (raw[i+1] & 0x3f))); i += 2
            elif b >> 4 == 0b1110:
                out.append(chr(((b & 0xf) << 12) | ((raw[i+1] & 0x3f) << 6) | (raw[i+2] & 0x3f))); i += 3
            else:
                i += 1
        return ''.join(out)
    # class_defs
    class_defs = struct.unpack_from('<I', data, 96)[0]
    # simpler: walk ALL class_defs, resolve name (arrays: off fields)
    str_off = struct.unpack_from('<I', data, 60)[0]
    type_off = struct.unpack_from('<I', data, 68)[0]
    meth_off = struct.unpack_from('<I', data, 92)[0]
    cdef_off = struct.unpack_from('<I', data, 100)[0]
    for i in range(class_defs):
        cd = cdef_off + 32*i
        cls_idx = struct.unpack_from('<I', data, cd)[0]
        ts = struct.unpack_from('<I', data, type_off + 4*cls_idx)[0]
        cname = get_str(struct.unpack_from('<I', data, str_off + 4*ts)[0])
        if cname != cls: continue
        cdoff = struct.unpack_from('<I', data, cd + 24)[0]
        if cdoff == 0: continue
        o = cdoff
        sf, inf, dm, vm, n = uleb(data, o); o = n
        uleb(data, o); o = n
        for _ in range(sf):
            _, o = uleb(data, o); _, o = uleb(data, o)
        for _ in range(inf):
            _, o = uleb(data, o); _, o = uleb(data, o)
        midx = 0
        for _ in range(dm):
            d, o = uleb(data, o); midx += d
            acc, o = uleb(data, o)
            m = meth_off + 8*midx
            mname = struct.unpack_from('<I', data, m + 4)[0]
            if get_str(struct.unpack_from('<I', data, str_off + 4*mname)[0]) == meth:
                code_off = struct.unpack_from('<I', data, o)[0]
                if code_off == 0: continue
                regsz, ins, outs, tries, dbg, insns_sz = struct.unpack_from('<6H', data, code_off)
                insns_bytes = insns_sz * 2
                tries_off = code_off + 16 + insns_bytes
                if insns_sz % 2 == 1: tries_off += 2
                print(f"method {meth}: insns={insns_sz} tries={tries}")
                for t in range(tries):
                    start, icount, handler = struct.unpack_from('<3I', data, tries_off + 12*t)
                    print(f"  try start_pc={start} insn_count={icount} handler_off={handler}")
                return


for name in zf.namelist():
    if not name.startswith("classes") or not name.endswith(".dex"): continue
    find_method(zf.read(name))
