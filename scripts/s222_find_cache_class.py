#!/usr/bin/env python3
"""S222-A: identify the REAL MultiParagraphLayoutCache class in dooz, its
density-field writer, and who constructs the (0,0) InlineDensity.

Steps:
1. Locate string constants: 'InlineDensity(', the ISE message, 'MultiParagraphLayoutCache'.
2. Find methods whose code references those string indices (const-string).
3. Identify the cache class (thrower) + the InlineDensity class (toString formatter).
4. List the cache class fields (find the density field), its methods that iput it.
5. Find constructors of the InlineDensity class and all invoke sites of them.
"""
import struct, zipfile, sys

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
z = zipfile.ZipFile(APK)
dex = z.read([n for n in z.namelist() if n.endswith('.dex')][0])

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80):
            break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
proto_size, proto_off = struct.unpack_from("<2I", dex, 0x48)
field_size, field_off = struct.unpack_from("<2I", dex, 0x50)
m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)

def str_at(si):
    off = str_off_arr[si]
    _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode("utf-8", "replace")

tds = [str_at(struct.unpack_from("<I", dex, type_off + t*4)[0]) for t in range(type_size)]

# method_id: (class_idx u16, proto_idx u16, name_idx u32)
mids = [struct.unpack_from("<IHH", dex, m_off + i*8) for i in range(m_size)]  # name_idx, class_idx? order: class_idx, proto_idx, name_idx
# actual DEX method_ids struct: class_idx u16, proto_idx u16, name_idx u32
mids = [struct.unpack_from("<HHI", dex, m_off + i*8) for i in range(m_size)]  # (class_idx, proto_idx, name_idx)
# proto_ids: shorty_idx u32, return_type_idx u32, parameters_off u32
protos = [struct.unpack_from("<3I", dex, proto_off + i*12) for i in range(proto_size)]
# field_ids: class_idx u16, type_idx u16, name_idx u32
fids = [struct.unpack_from("<HHI", dex, field_off + i*8) for i in range(field_size)]

def proto_str(pi):
    _, ret, params_off = protos[pi]
    ps = ""
    if params_off:
        n = struct.unpack_from("<I", dex, params_off)[0]
        ps = "".join(tds[struct.unpack_from("<H", dex, params_off + 4 + k*2)[0]] for k in range(n))
    return f"({ps}){tds[ret]}"

# string -> ids
targets = {}
for si in range(str_size):
    s = str_at(si)
    if "InlineDensity(" in s or "could not provide TextLayoutResult" in s or "MultiParagraphLayoutCache" in s:
        targets.setdefault(s, []).append(si)
for s, ids in targets.items():
    print(f"STRING[{ids}]: {s[:180]}")
stridx_map = {}
for s, ids in targets.items():
    for i in ids:
        stridx_map[i] = s

# walk classes -> find code units containing const-string with those indices
class_defs = []
for i in range(c_size):
    class_defs.append(struct.unpack_from("<IIIIIIII", dex, c_off + i*32))

def code_items_of(cls):
    """yield (mid, code_off, insns_u16s)"""
    _, _, _, _, sd_off = cls[3], cls[4], cls[5], cls[6], cls[7]
    return
# parse class_data_item
def parse_class_data(off):
    sf, o = uleb(dex, off); inf, o = uleb(dex, o); dm, o = uleb(dex, o); vm, o = uleb(dex, o)
    fields = []
    fi = 0
    for _ in range(sf):
        d, o = uleb(dex, o); fi += d
        _, o = uleb(dex, o)
        fields.append(fi)
    fi = 0
    for _ in range(inf):
        d, o = uleb(dex, o); fi += d
        _, o = uleb(dex, o)
        fields.append(fi)
    methods = []
    mi = 0
    for _ in range(dm):
        d, o = uleb(dex, o); mi += d
        acc, o = uleb(dex, o)
        co, o = uleb(dex, o)
        methods.append((mi, acc, co))
    for _ in range(vm):
        d, o = uleb(dex, o); mi += d
        acc, o = uleb(dex, o)
        co, o = uleb(dex, o)
        methods.append((mi, acc, co))
    return methods

hits = {}
for cls in class_defs:
    ci, acc, supi, ifc_off, sd_off = cls[0], cls[1], cls[2], cls[3], cls[6]
    cdesc = tds[ci]
    if sd_off == 0:
        continue
    for (mi, macc, coff) in parse_class_data(sd_off):
        if coff == 0:
            continue
        # code_item: registers u16, ins u16, outs u16, tries u16, debug u32, insns_size u32
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from("<4H2I", dex, coff)
        ic_off = coff + 16
        if insns_size == 0 or ic_off + insns_size*2 > len(dex):
            continue  # bogus code_item (misparse guard)
        insns = dex[ic_off:ic_off + insns_size*2]
        # scan with a FULL opcode-size table (naive +2 walk lands mid-instruction)
        SZT = [1]*256
        for op in range(0x04,0x08): SZT[op]=2
        SZT[0x13]=2; SZT[0x14]=3; SZT[0x16]=2; SZT[0x17]=3; SZT[0x18]=5; SZT[0x19]=2
        SZT[0x1a]=2; SZT[0x1b]=3
        SZT[0x1c]=2; SZT[0x1f]=2; SZT[0x20]=2
        SZT[0x24]=3; SZT[0x25]=3; SZT[0x26]=3
        SZT[0x29]=2; SZT[0x2a]=3; SZT[0x2b]=3; SZT[0x2c]=3
        for op in range(0x2d,0x32): SZT[op]=2
        for op in range(0x32,0x3e): SZT[op]=2
        for op in range(0x44,0x52): SZT[op]=2
        for op in range(0x52,0x60): SZT[op]=2
        for op in range(0x60,0x6e): SZT[op]=2
        for op in range(0x6e,0x73): SZT[op]=3
        for op in range(0x74,0x79): SZT[op]=3
        for op in range(0x90,0xb0): SZT[op]=2
        for op in range(0xd0,0xd4): SZT[op]=2
        for op in range(0xd5,0xe3): SZT[op]=2
        SZT[0xea]=2; SZT[0xeb]=2; SZT[0xec]=2; SZT[0xed]=2; SZT[0xee]=2; SZT[0xef]=2
        for op in range(0xf0,0xf2): SZT[op]=2
        SZT[0xfa]=3; SZT[0xfb]=3; SZT[0xfc]=3; SZT[0xfd]=3
        SZT[0xfe]=2; SZT[0xff]=2
        j = 0
        n = len(insns)
        while j + 1 < n:
            op = insns[j]
            step = SZT[op] * 2 if op != 0x00 else 2
            if op == 0x1A and j + 4 <= n:
                sidx = struct.unpack_from("<H", insns, j+1)[0]
                if sidx in stridx_map:
                    hits.setdefault(cdesc, []).append((mids[mi], sidx))
            elif op == 0x1B and j + 6 <= n:
                sidx = struct.unpack_from("<I", insns, j+1)[0]
                if sidx in stridx_map:
                    hits.setdefault(cdesc, []).append((mids[mi], sidx))
            elif op == 0x00 and j+1 < n:
                # nop / special payloads: align via the u16 payload sizes
                nxt = insns[j+1]
                if nxt == 0x0100 and j + 8 <= n:   # packed-switch payload
                    width = insns[j+2]//2; size = struct.unpack_from("<I", insns, j+4)[0]
                    step = 4 + 4 + size*(width*2) + 2 - 2
                    step = ((step + 1)//2)*2
                elif nxt == 0x0200 and j + 4 <= n:  # sparse-switch payload
                    size = struct.unpack_from("<I", insns, j+2)[0]
                    step = 2 + 2 + size*4 + size*2
                elif nxt == 0x0300 and j + 4 <= n:  # fill-array-data payload
                    width = insns[j+2]; size = struct.unpack_from("<I", insns, j+4)[0]
                    step = 4 + size*width
                else:
                    step = 2
            j += step if step else 2
for cdesc, lst in hits.items():
    print(f"\nCLASS {cdesc} referencing target strings:")
    for (mci, mpi, mn), sidx in lst:
        print(f"  {cdesc}->{str_at(mn)}{proto_str(mpi)}  uses[{stridx_map[sidx][:60]!r}]")
