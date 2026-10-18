#!/usr/bin/env python3
"""CONT-95: generic raw try-table probe — for class+method+pc(unit), parse the
raw DEX code_item tries and report coverage + handler types."""
import struct, sys
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK_PATH = "upload/telegram_official.apk"

def uleb(buf, pos):
    r = 0; s = 0
    while True:
        by = buf[pos]; pos += 1
        r |= (by & 0x7F) << s
        if not (by & 0x80): break
        s += 7
    return r, pos

def sleb(buf, pos):
    r = 0; s = 0
    while True:
        by = buf[pos]; pos += 1
        r |= (by & 0x7F) << s
        s += 7
        if not (by & 0x80): break
    if r & (1 << (s - 1)): r -= (1 << s)
    return r, pos

def probe(cls_name, meth_name, pc_units):
    a = APK(APK_PATH)
    for dex_name in a.get_dex_names():
        r = a.get_file(dex_name)
        if cls_name.encode() not in r: continue
        d = DalvikVMFormat(r)
        cls = next((c for c in d.get_classes() if c.get_name() == cls_name), None)
        if not cls: continue
        m = next((x for x in cls.get_methods() if x.get_name() == meth_name and x.get_code()), None)
        if not m:
            print(f"{cls_name}.{meth_name}: no code"); return
        code = m.get_code()
        off = code.get_off()
        b = r
        regs, ins_n, outs, tries_n = struct.unpack_from("<HHHH", b, off)
        debug_off, insns_n = struct.unpack_from("<II", b, off + 8)
        insns_bytes = insns_n * 2
        tries_start = off + 16 + insns_bytes
        if insns_n % 2 == 1: tries_start += 2
        handlers_start = tries_start + tries_n * 8
        # parse tries
        tries = []
        for i in range(tries_n):
            start, cnt, hoff = struct.unpack_from("<IHH", b, tries_start + i * 8)
            tries.append((start, start + cnt, hoff))
        # parse handler list (byte offsets relative to handlers_start)
        pos = handlers_start
        hsize, pos = uleb(b, pos)
        hmap = {}
        hbase = pos  # handler_off is relative to the START of the list STRUCTURE
        handlers_abs = []
        for i in range(hsize):
            hstart = pos
            sz, hpos = sleb(b, pos)
            entries = []
            for j in range(abs(sz)):
                tidx, hpos = uleb(b, hpos)
                addr, hpos = uleb(b, hpos)
                entries.append((tidx, addr))
            ca = None
            if sz <= 0:
                ca, hpos = uleb(b, hpos)
            hmap[pos - hbase] = (entries, ca)
            pos = hpos
        # resolve type names via type_ids
        string_ids_off, = struct.unpack_from("<I", b, 60)
        type_ids_off, = struct.unpack_from("<I", b, 68)
        def tname(tidx):
            di, = struct.unpack_from("<I", b, type_ids_off + 4 * tidx)
            sdo, = struct.unpack_from("<I", b, string_ids_off + 4 * di)
            p = sdo
            s = 0; ln = 0
            while True:
                by = b[p]; p += 1; ln |= (by & 0x7F) << s
                if not (by & 0x80): break
                s += 7
            end = b.index(b'\x00', p)
            return b[p:end].decode('utf-8', 'replace')
        print(f"{cls_name}.{meth_name} (dex={dex_name}) tries={tries_n} target_pc={pc_units}")
        covered = None
        for (s, e, hoff) in tries:
            if s <= pc_units < e:
                covered = (s, e, hoff)
                break
        if covered:
            s, e, hoff = covered
            entries, ca = hmap.get(hoff, ([], None))
            desc = []
            for tidx, addr in entries:
                desc.append(f"{tname(tidx)}@{addr}")
            if ca is not None:
                desc.append(f"<catch-all>@{ca}")
            print(f"  COVERED by try [{s}..{e}) handler_off={hoff} -> {desc}")
        else:
            near = [t for t in tries if t[1] <= pc_units]
            last = max(near, key=lambda t: t[1]) if near else None
            print(f"  NOT COVERED (nearest try ends at {last[1] if last else 'none'})")
        return
    print(f"{cls_name} not found")

if __name__ == "__main__":
    probe(sys.argv[1], sys.argv[2], int(sys.argv[3]))
